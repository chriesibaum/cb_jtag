import usb.core
import usb.util
import struct

from .cb_jtag_probe_base import CBJtagProbeBase
from .cb_jtag_probe_base import CBJtagProbeError, DeviceNotFoundError


import logging
log = logging.getLogger(__name__)



class UsbBusyError(CBJtagProbeError):
    pass


class InterfaceNotFoundError(CBJtagProbeError):
    pass


class ProtocolError(CBJtagProbeError):
    pass


class JtagProtocol:
    CMD_SCAN = 0x01
    CMD_NSRST_HIGH = 0x02
    CMD_NSRST_LOW = 0x03
    CMD_GET_FW_VERSION = 0x04
    CMD_GET_DEVICE_ID = 0x05
    FW_VERSION_PAYLOAD_LEN = 32
    STATUS_OK = 0x00
    HEADER_FMT_REQ = "<BBHI"
    HEADER_FMT_RSP = "<BBHI"

    @staticmethod
    def required_bytes(n_bits):
        return (n_bits + 7) // 8

    @classmethod
    def build_scan_request(cls, tdi_buf, tms_buf, n_bits):
        n_bytes = cls.required_bytes(n_bits)
        header = struct.pack(cls.HEADER_FMT_REQ, cls.CMD_SCAN, 0x00, 0x0000, n_bits)
        return header + bytes(tdi_buf[:n_bytes]) + bytes(tms_buf[:n_bytes])

    @classmethod
    def build_control_request(cls, cmd):
        return struct.pack(cls.HEADER_FMT_REQ, cmd, 0x00, 0x0000, 0)

    @classmethod
    def parse_scan_response(cls, rsp, n_bits):
        n_bytes = cls.required_bytes(n_bits)
        header_size = struct.calcsize(cls.HEADER_FMT_RSP)

        if len(rsp) < header_size:
            raise ProtocolError("short response header")

        status, flags, reserved, rsp_bits = struct.unpack(cls.HEADER_FMT_RSP, rsp[:header_size])

        if reserved != 0:
            raise ProtocolError(f"invalid reserved field in response: {reserved}")
        if status != cls.STATUS_OK:
            raise ProtocolError(f"device reported error status: {status}")
        if rsp_bits != n_bits:
            raise ProtocolError(f"response n_bits mismatch: expected {n_bits}, got {rsp_bits}")

        tdo_data = rsp[header_size:]
        if len(tdo_data) != n_bytes:
            raise ProtocolError("short TDO payload")

        return tdo_data

    @classmethod
    def parse_status_response(cls, rsp):
        header_size = struct.calcsize(cls.HEADER_FMT_RSP)
        if len(rsp) < header_size:
            raise ProtocolError("short response header")

        status, flags, reserved, rsp_bits = struct.unpack(cls.HEADER_FMT_RSP, rsp[:header_size])

        if reserved != 0:
            raise ProtocolError(f"invalid reserved field in response: {reserved}")
        if rsp_bits != 0:
            raise ProtocolError(f"response n_bits mismatch for control command: expected 0, got {rsp_bits}")
        if len(rsp) != header_size:
            raise ProtocolError("unexpected payload for control response")
        if status != cls.STATUS_OK:
            raise ProtocolError(f"device reported error status: {status}")

        return status, flags

    @classmethod
    def parse_firmware_version_response(cls, rsp):
        header_size = struct.calcsize(cls.HEADER_FMT_RSP)
        expected_n_bits = cls.FW_VERSION_PAYLOAD_LEN * 8
        expected_len = header_size + cls.FW_VERSION_PAYLOAD_LEN

        if len(rsp) < header_size:
            raise ProtocolError("short response header")

        status, flags, reserved, rsp_bits = struct.unpack(cls.HEADER_FMT_RSP, rsp[:header_size])

        if reserved != 0:
            raise ProtocolError(f"invalid reserved field in response: {reserved}")
        if status != cls.STATUS_OK:
            raise ProtocolError(f"device reported error status: {status}")
        if rsp_bits != expected_n_bits:
            raise ProtocolError(
                f"response n_bits mismatch for firmware version: expected {expected_n_bits}, got {rsp_bits}"
            )
        if len(rsp) != expected_len:
            raise ProtocolError(
                f"invalid firmware version payload length: expected {expected_len}, got {len(rsp)}"
            )

        payload = rsp[header_size:]
        version = payload.split(b"\x00", 1)[0].decode("ascii", errors="strict")
        return version, flags

    @classmethod
    def parse_device_id_response(cls, rsp):
        header_size = struct.calcsize(cls.HEADER_FMT_RSP)
        if len(rsp) < header_size:
            raise ProtocolError("short response header")

        status, flags, reserved, rsp_bits = struct.unpack(cls.HEADER_FMT_RSP, rsp[:header_size])

        if reserved != 0:
            raise ProtocolError(f"invalid reserved field in response: {reserved}")
        if status != cls.STATUS_OK:
            raise ProtocolError(f"device reported error status: {status}")
        if rsp_bits == 0 or rsp_bits % 8 != 0:
            raise ProtocolError(f"invalid n_bits in device ID response: {rsp_bits}")

        n_bytes = rsp_bits // 8
        payload = rsp[header_size:]
        if len(payload) != n_bytes:
            raise ProtocolError(
                f"device ID payload length mismatch: expected {n_bytes}, got {len(payload)}"
            )

        return bytes(payload)

class CBJtagProbe(CBJtagProbeBase):
    DEFAULT_PREFERRED_DEVICES = (
        (0x2FE3, 0x0001),
    )

    def __init__(self, preferred_devices=DEFAULT_PREFERRED_DEVICES, interface_class=0xFF):
        self.interface_class = interface_class
        self.preferred_devices = tuple(preferred_devices)
        self.device_matcher = (
            lambda dev: CBJtagProbe._has_matching_bulk_pair(dev, self.interface_class)
        )

        self.dev = None
        self._claimed = False

    def open(self, device_id=None):
        """
        Open a connection to the probe with the specified ID.
        """

        devices = self._detect_devices()
        if not devices:
            raise DeviceNotFoundError("No compatible Chriesibaum JTAG probes found. Check connections and drivers.")

        if device_id is None:
            raise ValueError("Specify an ID to select a probe.")


        self.dev = next((d for d in devices if (d.serial_number == device_id or f"{d.bus}:{d.address}" == device_id)), None)

        cfg = self._get_configuration(self.dev)
        if cfg is None:
            raise UsbBusyError(
                "Unable to access USB configuration (device busy). Close serial monitors and retry."
            )

        self.ep_out, self.ep_in, self.intf_num, self.interface_debug = self._select_bulk_interface(
            cfg,
            interface_class=self.interface_class,
        )
        if self.ep_out is None or self.ep_in is None:
            details = "; ".join(self.interface_debug) if self.interface_debug else "no interfaces"
            raise InterfaceNotFoundError(
                "Vendor bulk IN/OUT endpoints not found. "
                f"Detected interfaces: {details}. "
                "This usually means device is running CDC-only firmware; flash the custom bulk JTAG firmware."
            )

        self._claim_interface()

    @staticmethod
    def _select_bulk_interface(cfg, interface_class):
        ep_out = None
        ep_in = None
        intf_num = None
        interface_debug = []

        for intf in cfg:
            interface_debug.append(
                f"if{intf.bInterfaceNumber}: class=0x{intf.bInterfaceClass:02x} "
                f"sub=0x{intf.bInterfaceSubClass:02x} proto=0x{intf.bInterfaceProtocol:02x}"
            )
            if intf.bInterfaceClass != interface_class:
                continue

            out_ep = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: (
                    usb.util.endpoint_direction(e.bEndpointAddress)
                    == usb.util.ENDPOINT_OUT
                )
                and (usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK),
            )

            in_ep = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: (
                    usb.util.endpoint_direction(e.bEndpointAddress)
                    == usb.util.ENDPOINT_IN
                )
                and (usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK),
            )

            if out_ep is not None and in_ep is not None:
                ep_out = out_ep
                ep_in = in_ep
                intf_num = intf.bInterfaceNumber
                break

        return ep_out, ep_in, intf_num, interface_debug

    def _claim_interface(self):
        if self.dev.is_kernel_driver_active(self.intf_num):
            self.dev.detach_kernel_driver(self.intf_num)
        usb.util.claim_interface(self.dev, self.intf_num)
        self._claimed = True

    def close(self):
        if self._claimed:
            usb.util.release_interface(self.dev, self.intf_num)
            self._claimed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    @staticmethod
    def _has_matching_bulk_pair(dev, interface_class):
        cfg = CBJtagProbe._get_configuration(dev)
        if cfg is None:
            return False

        try:
            ep_out, ep_in, _, _ = CBJtagProbe._select_bulk_interface(cfg, interface_class)
            return ep_out is not None and ep_in is not None
        except usb.core.USBError:
            return False

    @staticmethod
    def _get_configuration(dev):
        try:
            return dev.get_active_configuration()
        except usb.core.USBError:
            pass

        try:
            dev.set_configuration()
            return dev.get_active_configuration()
        except usb.core.USBError:
            return None

    def _detect_devices(self):
        devices = []
        for vid, pid in self.preferred_devices:
            devs = usb.core.find(idVendor=vid, idProduct=pid, find_all=True)
            for dev in devs:
                if dev is not None and self.device_matcher(dev):
                    devices.append(dev)
        return devices

    @staticmethod
    def _required_bytes(n_bits):
        return JtagProtocol.required_bytes(n_bits)

    @staticmethod
    def _as_mutable_view(buf):
        if isinstance(buf, bytearray):
            return memoryview(buf)
        if isinstance(buf, memoryview) and not buf.readonly:
            return buf
        raise TypeError("tdo_buf must be a writable bytearray or writable memoryview")

    def get_version(self):
        payload = JtagProtocol.build_control_request(JtagProtocol.CMD_GET_FW_VERSION)
        self.ep_out.write(payload)

        expected_rsp = struct.calcsize(JtagProtocol.HEADER_FMT_RSP) + JtagProtocol.FW_VERSION_PAYLOAD_LEN
        rsp = bytes(self.ep_in.read(expected_rsp, timeout=1000))
        version, _ = JtagProtocol.parse_firmware_version_response(rsp)
        return version

    def get_device_id(self):
        """
        Returns the raw device ID bytes as returned by the probe firmware. The format and meaning of these bytes is determined by the firmware and is not standardized.
        """
        payload = JtagProtocol.build_control_request(JtagProtocol.CMD_GET_DEVICE_ID)
        self.ep_out.write(payload)
        max_rsp = struct.calcsize(JtagProtocol.HEADER_FMT_RSP) + 512
        rsp = bytes(self.ep_in.read(max_rsp, timeout=1000))
        return JtagProtocol.parse_device_id_response(rsp)

    def get_device_id_str(self):
        """
        Returns the device ID as a hex string, for easier display and logging.
        """
        device_id_bytes = self.get_device_id()
        device_id_str = device_id_bytes.hex().upper()
        return device_id_str

    def set_sys_reset_pin_high(self):
        payload = JtagProtocol.build_control_request(JtagProtocol.CMD_NSRST_HIGH)
        self.ep_out.write(payload)
        expected_rsp = struct.calcsize(JtagProtocol.HEADER_FMT_RSP)
        rsp = bytes(self.ep_in.read(expected_rsp, timeout=1000))
        JtagProtocol.parse_status_response(rsp)
        return True

    def set_sys_reset_pin_low(self):
        payload = JtagProtocol.build_control_request(JtagProtocol.CMD_NSRST_LOW)
        self.ep_out.write(payload)
        expected_rsp = struct.calcsize(JtagProtocol.HEADER_FMT_RSP)
        rsp = bytes(self.ep_in.read(expected_rsp, timeout=1000))
        JtagProtocol.parse_status_response(rsp)
        return True

    def jtag_write_read(self, tdi_buf, tdo_buf, tms_buf, n_bits):
        if n_bits <= 0:
            raise ValueError("n_bits must be > 0")

        n_bytes = self._required_bytes(n_bits)
        if len(tdi_buf) < n_bytes:
            raise ValueError("tdi_buf too small for n_bits")
        if len(tms_buf) < n_bytes:
            raise ValueError("tms_buf too small for n_bits")

        tdo_view = self._as_mutable_view(tdo_buf)
        if len(tdo_view) < n_bytes:
            raise ValueError("tdo_buf too small for n_bits")

        payload = JtagProtocol.build_scan_request(tdi_buf, tms_buf, n_bits)

        self.ep_out.write(payload)

        expected_rsp = struct.calcsize(JtagProtocol.HEADER_FMT_RSP) + n_bytes
        rsp = bytes(self.ep_in.read(expected_rsp, timeout=1000))
        tdo_data = JtagProtocol.parse_scan_response(rsp, n_bits)

        tdo_view[:n_bytes] = tdo_data
        return n_bytes


    def jtag_flush(self):
        return True

    def get_probes(self):
        devices = self._detect_devices()

        probes = {}
        for dev in devices:
            try:
                serial = dev.serial_number
            except usb.core.USBError:
                serial = f"{dev.bus}:{dev.address}"
            probes[serial] = {
                'id': serial,
                'manufacturer': dev.manufacturer or "Unknown",
                'product': dev.product or f"{dev.idVendor:04X}:{dev.idProduct:04X}",
                'driver': self.__class__.__name__,
            }

        return probes

    def easy_setup_probe(self, probe_id=None):
        """Easy setup of the probe by automatically detecting connected probes and connecting to the first one found."""
        probes = self.get_probes()
        if not probes:
            log.error("No compatible Chriesibaum JTAG probes found. Check connections and drivers.")
            raise DeviceNotFoundError("No compatible Chriesibaum JTAG probes found. Check connections and drivers.")

        if probe_id is None:
            probe = next(iter(probes))
            probe_id = probes[probe]['id']
        else:
            probe = next((p for p in probes if probes[p]['id'] == probe_id), None)
            if probe is None:
                log.error(f"No probe found with ID: {probe_id}")
                raise DeviceNotFoundError(f"No probe found with ID: {probe_id}")

        log.info(f'Connecting to probe with id: {probe_id} using driver {self.__class__.__name__}')

        self.open(probe_id)
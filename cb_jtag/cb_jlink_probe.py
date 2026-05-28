import ctypes
import sys

from pylink import JLink
from pylink import enums

from .cb_jtag_probe_base import CBJtagProbeBase
from .cb_jtag_probe_base import DeviceNotFoundError
from .cb_jtag import CBJtagError

import logging
log = logging.getLogger(__name__)

class CBJLinkProbe(JLink, CBJtagProbeBase):

    def __init__(self, lib=None):
        super().__init__(lib=lib)

        self.detailed_log_handler = None

    def get_version(self):
        """Get the version of the J-Link DLL.
        Returns:
            str: The version string of the J-Link DLL.
        """
        version = f'{self.version}'
        return version

    def get_device_id_str(self):
        """Get the device ID string of the connected J-Link probe.
        Returns:
            str: The device ID string of the connected J-Link probe.
        """
        id_str = f'{self.device_id}'
        return id_str

    def set_sys_reset_pin_high(self):
        self.set_reset_pin_high()

    def set_sys_reset_pin_low(self):
        self.set_reset_pin_low()

    def jtag_write_read(self,
                        tdi_buf,
                        tdo_buf,
                        tms_buf,
                        n_bits):

        ctdo_buf = (ctypes.c_ubyte * len(tdo_buf))()

        res = self._dll.JLINKARM_JTAG_StoreGetRaw(tdi_buf,
                                                  ctdo_buf,
                                                  tms_buf,
                                                  n_bits)
        if res < 0:         # pragma: no cover
            raise CBJtagError(f'dll call JLINKARM_JTAG_StoreGetRaw failed with error code: {res}')


        res = self._dll.JLINKARM_JTAG_SyncBits()
        if res < 0:         # pragma: no cover
            raise CBJtagError(f'dll call JLINKARM_JTAG_SyncBits failed with error code: {res}')

        # Copy the data from the ctypes buffer to the provided tdo_buf
        # todo: @SEGGER: would be nice if the JLINKARM_JTAG_StoreGetRaw function could write directly into a provided buffer to avoid this copy step
        tdo_buf[:] = ctdo_buf[:len(tdo_buf)]

    def get_probes(self):
        emulators =  self.connected_emulators()

        probes = {}
        for emu in emulators:
            id_str = str(emu.SerialNumber)
            probes[id_str] = {
                'id': id_str,
                'manufacturer': 'SEGGER',
                'product': emu.acProduct.decode('utf-8'),
                'driver': self.__class__.__name__,
            }

        return probes

    def easy_setup_probe(self, probe_id=None, speed=4000):
        """Easy setup of the J-Link probe by automatically detecting connected J-Link
        probes and connecting to the first one found."""

        emulators = self.connected_emulators()

        # Print the serial number of all emulators
        log.info('Connected J-Link emulator(s):')
        for emu in emulators:
            log.info(f'  S/N: {emu.SerialNumber}')

        # Get the first emulator S/N to connect to it
        if not emulators:   # pragma: no cover
            log.error('No J-Link emulators found!')
            raise DeviceNotFoundError("No J-Link emulators found!")
        if probe_id is None:
            self.device_id = emulators[0].SerialNumber
        else:
            # Find the emulator with the specified S/N
            emu = next((e for e in emulators if str(e.SerialNumber) == probe_id), None)
            if emu is None:    # pragma: no cover
                log.error(f'No J-Link emulator found with S/N: {probe_id}')
                raise DeviceNotFoundError(f"No probe found with ID: {probe_id}")

            self.device_id = probe_id

        log.info(f'Connecting to probe with id: {probe_id} using driver {self.__class__.__name__}')

        # Open a connection to the J-Link adapter
        self.open(self.device_id)
        self.set_speed(speed)
        self.set_tif(enums.JLinkInterfaces.JTAG)

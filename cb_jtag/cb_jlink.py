import ctypes
import sys

from pylink import JLink
from pylink import enums

from .cb_jtag_probe_base import CBJtagProbeBase
from .cb_jtag import CBJtagError

import logging
log = logging.getLogger(__name__)

class CBJLink(JLink, CBJtagProbeBase):

    def __init__(self, lib=None):
        super().__init__(lib=lib)

    def get_version(self):
        """Get the version of the J-Link DLL.
        Returns:
            str: The version string of the J-Link DLL.
        """
        version = f'{self.version}'
        return version


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


    def easy_setup_emulator(self, speed=4000):

        emulators = self.connected_emulators()

        # Print the serial number of all emulators
        log.info('Connected J-Link emulator(s):')
        for emu in emulators:
            log.info(f'  S/N: {emu.SerialNumber}')

        # Get the first emulator S/N to connect to it
        if not emulators:   # pragma: no cover
            log.error('No J-Link emulators found!')
            sys.exit(-1)
        serial_no = emulators[0].SerialNumber

        # Open a connection to the J-Link adapter
        self.open(serial_no)
        self.set_speed(speed)
        self.set_tif(enums.JLinkInterfaces.JTAG)

from .cb_jtag_iface_base import CBJtagIfaceBase
from .cb_jtag import CBJtagError

from pylink import JLink
from pylink import enums

import ctypes
import math



class CBJLink(JLink, CBJtagIfaceBase):

    def __init__(self, lib=None):
        super().__init__(lib=lib)


    def jtag_write_read(self,
                        tdi_buf,
                        tdo_buf,
                        tms_buf,
                        n_bits):

        res = self._dll.JLINKARM_JTAG_StoreGetRaw(tdi_buf,
                                                  tdo_buf,
                                                  tms_buf,
                                                  n_bits)
        if res < 0:
            raise CBJtagError(f"dll call JLINKARM_JTAG_StoreGetRaw failed with error code: {res}")


        res = self._dll.JLINKARM_JTAG_SyncBits()
        if res < 0:
            raise CBJtagError(f"dll call JLINKARM_JTAG_SyncBits failed with error code: {res}")

    # todo: @SEGGER: would be nice to have a JLINKARM_JTAG_Reset() function
    # def sys_reset(self, reset_delay_ms=100):
    #     """Reset the JTAG interface."""

    #     self._dll.JLINK_SetResetDelay(reset_delay_ms)

    #     res = self._dll.JLINK_JTAG_Reset()
    #     if res < 0:
    #         raise errors.JLinkException(res)



    def easy_setup_emulator(self, speed=4000):

        emulators = self.connected_emulators()

        # Print the serial number of all emulators
        print('Connected J-Link emulator(s):')
        for emu in emulators:
            print(f'  S/N: {emu.SerialNumber}')

        # Get the first emulator S/N to connect to it
        if not emulators:
            print('No J-Link emulators found!')
            exit(-1)
        serial_no = emulators[0].SerialNumber

        # Open a connection to the J-Link adapter
        self.open(serial_no)
        self.set_speed(speed)
        self.set_tif(enums.JLinkInterfaces.JTAG)

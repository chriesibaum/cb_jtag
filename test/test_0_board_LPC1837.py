import pytest
import time

from .test_base import CBJtagBase
from cb_jtag.cb_bsr import CBBsrPinNotifier, CBRsrOutput, CBRsrOutputToggler


class Test_NXP_LPC1837(CBJtagBase):
    bsdl_file = './bsdl_files/lpc1857fet256_revA_20180227-v1.bsd'
    exp_num_taps = 2
    exp_idcodes = [0x4BA00477, 0x16469041]

    def setup_io(self):
        self.in_P1_10_pin = ''
        self.led_P1_10_toggling = 0

        self.pin_P1_10_tout = CBRsrOutputToggler(self.bsdl, 'P1_10', toggle_time=2.5)
        self.bsr.add_pin(self.pin_P1_10_tout)

        self.pin_P1_10_in = CBBsrPinNotifier(self.bsdl, 'P1_10',
                                             cb=self.pin_P1_10_changed_cb, cb_parent=self)
        self.bsr.add_pin(self.pin_P1_10_in)


    def pin_P1_10_changed_cb(self, pin, val):
        print(f'Callback: Pin {pin} changed to {val}')
        self.in_P1_10_pin = pin
        self.led_P1_10_toggling += 1

    def test_010_toggle_led(self):
        print('Testing LED toggle on P1_10')

        time.sleep(1)

        assert self.in_P1_10_pin == 'P1_10', 'LED P1_10 callback not called'
        assert self.led_P1_10_toggling >= 5, 'LED P1_10 did not toggle'

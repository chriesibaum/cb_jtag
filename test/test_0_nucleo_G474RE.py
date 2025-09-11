import pytest
import time

from .test_base import CBJtagBase
from cb_jtag.cb_bsr import CBBsrPinNotifier, CBRsrOutput, CBRsrOutputToggler


class Test_Nucleo_G474RE(CBJtagBase):
    bsdl_file = './bsdl_files/STM32G471_473_474_483_484_LQFP64.bsdl'
    exp_num_taps = 2
    exp_idcodes = [0x4BA00477, 0x16469041]

    def setup_io(self):
        self.led_PA5_pin = ''
        self.led_PA5_toggling = 0

        # setup pin PA5 as output toggler and notifier
        self.led_PA5_tout = CBRsrOutputToggler(self.bsdl, 'PA5', toggle_time=0.1)
        self.bsr.add_pin(self.led_PA5_tout)

        self.led_PA5_in = CBBsrPinNotifier(self.bsdl, 'PA5',
                                           cb=self.led_PA5_changed_cb, cb_parent=self)
        self.bsr.add_pin(self.led_PA5_in)

        #  setup pin PC4 as output
        self.pc4_out = CBRsrOutput(self.bsdl, 'PC4')
        self.bsr.add_pin(self.pc4_out)

        # setup pin PC5 as input notifier
        self.pc5_in = CBBsrPinNotifier(self.bsdl, 'PC5')
        self.bsr.add_pin(self.pc5_in)


    def test_010_read_bsr(self):
        print('Testing reading BSR register')

        for i in range(3):
            time.sleep(0.1)
            bsr = self.jtag.read_bsr(0, 0b00010)

        time.sleep(0.1)

        assert bsr is not None, 'Failed to read BSR register'
        print(f' BSR: {bsr:076x}')


    def led_PA5_changed_cb(self, pin, val):
        self.led_PA5_pin = pin
        self.led_PA5_toggling += 1

    def test_020_toggle_led(self):
        print('Testing LED toggle on PA5')

        time.sleep(1)

        assert self.led_PA5_pin == 'PA5', 'LED PA5 callback not called'
        assert self.led_PA5_toggling >= 5, 'LED PA5 did not toggle'

    def test_021_pin_roundtrip(self):
        print('Testing pin roundtrip PC4 -> PC5')

        for i in range(5):
            print(f' Roundtrip test iteration {i}')
            # Set PC4 high
            self.pc4_out.set_val(1)
            time.sleep(0.2)
            assert self.pc5_in.val == 1, 'PC5 did not read high when PC4 set high'

            # Set PC4 low
            self.pc4_out.set_val(0)
            time.sleep(0.2)
            assert self.pc5_in.val == 0, 'PC5 did not read low when PC4 set low'


    def test_022_pin_set_clear(self):

        print('Testing pin set/clear on PC4 -> PC5')
        # Set PC4 (set high)
        self.pc4_out.set_val(1)
        time.sleep(0.2)
        assert self.pc5_in.get_val() == 1, 'PC5 did not read high when PC4 set'

        # Clear PC4 (set low)
        self.pc4_out.clear_val()
        time.sleep(0.2)
        assert self.pc5_in.get_val() == 0, 'PC5 did not read low when PC4 cleared'

    def test_030_callbacks(self):
        print('Testing callbacks on PC5 input pin')

        self.pc5_in_cb_val = 0

        def callback(pin, val):
            print(f' Callback: Pin {pin} changed to {val}')
            self.pc5_in_cb_val = val

        self.pc5_in.set_cb(callback)

        self.pc4_out.set_val(1)
        time.sleep(0.2)
        assert self.pc5_in.val == 1, 'PC5 did not read high when PC4 set high'
        assert self.pc5_in_cb_val == 1, 'PC5 callback not called on high'

        self.pc4_out.clear_val()
        time.sleep(0.2)
        assert self.pc5_in.val == 0, 'PC5 did not read low when PC4 set low'
        assert self.pc5_in_cb_val == 0, 'PC5 callback not called on low'

    def test_040_verboseity(self):
        print('Testing BSR verbosity setting')

        self.jtag.set_verbose(True)
        self.bsr.set_verbose(3)
        self.led_PA5_tout.set_verbose(True)
        self.pc4_out.set_verbose(True)
        self.pc5_in.set_verbose(True)

        time.sleep(0.01)

        self.jtag.set_verbose(False)
        self.bsr.set_verbose(True)

        self.pc4_out.set_val(1)

        time.sleep(1)

        self.led_PA5_tout.set_verbose(False)
        self.pc4_out.set_verbose(False)
        self.pc5_in.set_verbose(False)



# class Test_NXP(CBJtagBase):
#     pass
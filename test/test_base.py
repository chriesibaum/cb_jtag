
import time
from cb_bsdl_parser.cb_bsdl import CBBsdl

from cb_jtag import CBJLink
from cb_jtag import CBJtag
from cb_jtag.cb_bsr import CBBsr


class CBJtagBase:
    bsdl_file = ''
    exp_num_taps = 1
    exp_idcodes = [0]

    @classmethod
    def setup_class(self):
        print('setup_class')
        self.setup(self)
        self.setup_io(self)
        self.start_bs(self)

    def setup(self):
        # Initialize J-Link connection
        self.jlink = CBJLink()
        self.jlink.easy_setup_emulator()

        # Setup the JTAG interface for boundary-scan operations
        self.jtag = CBJtag(jtag_iface=self.jlink)

        # Hold the reset pin low for STM32xxx
        self.jlink.set_reset_pin_low()

        # Reset the JTAG TAP controller
        self.jtag.tap_reset()
        self.bsdl = CBBsdl(self.bsdl_file)

        # Get the number of TAPs in the JTAG chain
        self.num_taps = self.jtag.get_num_taps()

        # Read and display the IDCODEs of all TAPs
        self.id_codes = self.jtag.get_tap_id_code(self.num_taps)

        # Configure IR and BSR lengths based on BSDL file
        self.jtag.set_ir_lengths([5, 4])
        self.jtag.set_bsr_lengths([self.bsdl.get_bsr_len(), 0])

        # Initialize boundary-scan register interface
        self.bsr = CBBsr(self.jtag, verbose=1)


    def setup_io(self): # pragma: no cover
        raise NotImplementedError("This method should be implemented by subclasses.")

    def start_bs(self):
        self.bsr.config_pins()
        self.bsr.start()
        self.bsr.enable()

    def stop_bs(self):
        self.bsr.disable()
        time.sleep(0.1) # wait for the bsr thread to disable/halt
        self.bsr.stop()
        self.bsr.deconfig_pins()

    @classmethod
    def teardown_class(self):
        "Runs at end/teardown of class"
        print('teardown_class')
        self.stop_bs(self)
        self.jlink.set_reset_pin_high()
        self.jtag.close()

    def setup_method(self):
        """Called before each test method."""
        print('setup_method')


    def teardown_method(self):
        """Called after each test method."""
        print('teardown_method')


    def test_000_jtag_connection(self):
        print(f'Testing JTAG connection')
        # num_taps = self.jtag.get_num_taps()
        assert self.num_taps == self.exp_num_taps, "No TAPs found in JTAG chain"

    def test_001_jtag_idcodes(self):
        print('Testing JTAG IDCODEs')
        # id_codes = self.jtag.get_tap_id_code(self.exp_num_taps)

        print('Detected TAPs with IDCODEs:')
        for id_code, exp_id_code in zip(self.id_codes, self.exp_idcodes):
            print(f'TAP {self.id_codes.index(id_code)}: IDCODE: 0x{id_code:08X}, expected: 0x{exp_id_code:08X}')
            assert id_code == exp_id_code, f'IDCODE mismatch: {id_code} != {exp_id_code}'

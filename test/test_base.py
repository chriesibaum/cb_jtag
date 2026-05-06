import pytest
import time
from cb_bsdl_parser.cb_bsdl import CBBsdl

from cb_jtag import CBJLink
from cb_jtag import CBJtagProbe
from cb_jtag import CBJtag
from cb_jtag.cb_bsr import CBBsr


def get_test_params():
    # with open(test_params_file, 'r') as yaml_file:
    #     params = yaml.safe_load(yaml_file)

    # print("Test parameters loaded:")
    # for key, value in params.items():
    #     print(f"{key}: {value}")


    jlink_probe = CBJLink()
    jlink_probe.easy_setup_emulator()
    jlink_probe.set_speed(5)     # set J-Link speed to 5 kHz to be safe


    cb_jtag_probe = CBJtagProbe()

    params = {}
    params[0] = {'jtag_probe_name': 'CBJtagProbe',
                 'jtag_probe': cb_jtag_probe}

    params[1] = {'jtag_probe_name': 'CBJLink',
                 'jtag_probe': jlink_probe}


    for param in params:
        yield params[param]

    print("All test parameters have been used, cleaning up probes")
    del jlink_probe
    del cb_jtag_probe


class CBJtagBase:
    bsdl_file = ''
    exp_num_taps = 1
    exp_idcodes = [0]
    exp_num_taps = 0

    @pytest.fixture(scope='class', autouse=True, params=get_test_params())
    def class_probe_context(self, request):
        cls = request.cls
        print(f"setup_class for JTAG probe: {request.param['jtag_probe_name']}")
        cls.jtag_probe = request.param['jtag_probe']

        cls.setup(cls)
        cls.setup_io(cls)
        cls.start_bs(cls)

        yield

        cls.stop_bs(cls)
        cls.jtag.set_sys_reset_pin_high()
        cls.jtag.close()


    def setup(self):
        # Setup the JTAG probe for boundary-scan operations
        self.jtag = CBJtag(jtag_probe=self.jtag_probe)

        # Hold the reset pin low for STM32xxx
        self.jtag.set_sys_reset_pin_low()

        # Reset the JTAG TAP controller
        self.jtag.tap_reset()
        self.bsdl = CBBsdl(self.bsdl_file)

        # Get the number of TAPs in the JTAG chain
        self.taps_in_chain = self.jtag.get_taps_in_chain()

        # Read and display the IDCODEs of all TAPs
        self.id_codes = self.jtag.get_tap_id_code(self.taps_in_chain)

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
        time.sleep(0.5) # wait for the bsr thread to disable/halt
        self.bsr.stop()
        self.bsr.deconfig_pins()


    def test_000_jtag_connection(self):
        print(f'Testing JTAG connection')
        num_taps = self.jtag.get_taps_in_chain()
        assert num_taps == self.exp_num_taps, \
            f"Number of TAPs mismatch: {num_taps} != {self.exp_num_taps}"

    def test_001_jtag_idcodes(self):
        print('Testing JTAG IDCODEs')
        # id code is read in setup() and stored to test it here as
        # the bsr is already running at this point, so we can not read
        # the id codes again here without stopping the bsr first
        for id_code, exp_id_code in zip(self.id_codes, self.exp_idcodes):
            print(f'TAP {self.id_codes.index(id_code)}: IDCODE: 0x{id_code:08X}, expected: 0x{exp_id_code:08X}')
            assert id_code == exp_id_code, f'IDCODE mismatch: {id_code} != {exp_id_code}'

    def test_002_bsr_running(self):
        print('Testing BSR running')
        time.sleep(1)
        assert self.bsr.get_running() == True, 'BSR thread not running'

    def test_003_bsr_enable_disable(self):
        print('Testing BSR enable/disable')
        self.bsr.disable()
        time.sleep(0.1) # wait for the bsr thread to disable/halt
        assert self.bsr.get_running() == False, 'BSR thread not running after disable'

        self.bsr.enable()
        time.sleep(0.1) # wait for the bsr thread to enable/start
        assert self.bsr.get_running() == True, 'BSR thread running again after enable'


    def test_004_get_probe_version(self):
        print('Testing JTAG probe version')
        version = self.jtag.get_probe_version()
        print(f'JTAG probe version: {version}')
        assert version is not None, 'Failed to get JTAG probe version'


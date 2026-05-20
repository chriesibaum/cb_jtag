#!/usr/bin/env python3

# cb_jtag demo for the NUCLEO-G474RE board

import time
from cb_jtag import CBJtag
from cb_jtag import CBJLink
from cb_jtag import CBBsr
from cb_jtag import CBBsrPinNotifier
from cb_jtag import CBRsrOutput
from cb_jtag import CBRsrOutputToggler
from cb_bsdl_parser import CBBsdl
from cb_jtag.cb_jtag_probe import CBJtagProbe
from key_stroke import *


# Define the BSDL files for the target device and the Cortex-M core
# Note: The STM32G474RE has implemented 2 JTAG TAPs, the first TAP corresponds
# to the STM32G474RE microcontroller for boundary-scan operations,
# and the second TAP corresponds to the Cortex-M4 core for debugging purposes.

bsdl_file_0 = './bsdl_files/STM32G471_473_474_483_484_LQFP64.bsdl'
bsdl_file_1 = './bsdl_files/CORTEXMX.bsdl'


def pin_changed_cb(pin, val):
    print(f'Pin {pin:<5s} changed to {val}')


def main():
    # Initialize J-Link connection

    # select the probe/jtag adapter to use (J-Link or CBJtagProbe)
    # probe = CBJLink()
    # probe.easy_setup_emulator()

    probe = CBJtagProbe()

    # Setup the JTAG interface for boundary-scan operations
    jtag = CBJtag(jtag_probe=probe)

    print(f'Probe Version: {jtag.get_probe_version()}')
    print(f'Device ID: {jtag.get_probe_id_str()}')

    bsdl_0 = CBBsdl(bsdl_file_0)
    bsdl_1 = CBBsdl(bsdl_file_1, run_checks=False)

    # Hold the reset pin low for STM32xxx
    jtag.set_sys_reset_pin_low()
    # Reset the JTAG TAP controller
    jtag.tap_reset()

    # Get the number of TAPs in the JTAG chain
    num_taps = jtag.get_taps_in_chain()
    print(f'\nNumber of TAPs in JTAG chain: {num_taps}' )

    # Read and display the IDCODEs of all TAPs
    id_codes = jtag.get_tap_id_code(num_taps)
    print('Detected TAPs with IDCODEs:')
    for i, idcode in enumerate(id_codes):
        print(f'  TAP {i}: '
              f'IDCODE: 0x{idcode:08X}')


    # Configure IR and BSR lengths based on BSDL file
    jtag.set_target_device_tap(0)
    jtag.set_ir_lengths([bsdl_0.get_instr_len(),
                         bsdl_1.get_instr_len()])
    jtag.set_bsr_lengths([bsdl_0.get_bsr_len(),
                          bsdl_1.get_bsr_len()])

    inst_extest = bsdl_0.get_instr_opcode('EXTEST')
    print(f'\nInstruction code for EXTEST: 0b{inst_extest:05b}')

    # Initialize boundary-scan register interface
    bsr = CBBsr(jtag, verbose=1, inst_extest=inst_extest)
    # Configure pins for boundary-scan operations
    led_pin_tout = CBRsrOutputToggler(bsdl_0, 'PA5', toggle_time = 0.1)
    led_pin_in = CBBsrPinNotifier(bsdl_0, 'PA5',  cb=pin_changed_cb)
    btn_pin_in = CBBsrPinNotifier(bsdl_0, 'PC13', cb=pin_changed_cb)

    bsr.add_pin(led_pin_tout)
    bsr.add_pin(led_pin_in)
    bsr.add_pin(btn_pin_in)

    # Finally, configure and start the boundary-scan operations
    bsr.config_pins()
    bsr.start()
    bsr.enable()

    k = KeyStroke()
    print('\nStarting boundary-scan operations')
    print('Press ESC to terminate!')
    while True:
        # check whether a key from the list has been pressed
        if k.check(['\x1b', 'q', 'x']):
            break
        time.sleep(0.1)

    # Gracefully stop boundary-scan operations and clean up
    bsr.stop()
    bsr.deconfig_pins()
    jtag.set_sys_reset_pin_high() # do do: move this function into CBJTAG class
    jtag.close()



# Run the main function if this script is executed
if __name__ == '__main__':
    main()

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
from key_stroke import *


bsdl_file = './bsdl_files/STM32G471_473_474_483_484_LQFP64.bsdl'


def pin_changed_cb(pin, val):
    print(f'Pin {pin:<5s} changed to {val}')


def main():
    # Initialize J-Link connection
    jlink = CBJLink()
    jlink.easy_setup_emulator()

    # Setup the JTAG interface for boundary-scan operations
    jtag = CBJtag(jtag_iface=jlink)
    bsdl = CBBsdl(bsdl_file)

    # Hold the reset pin low for STM32xxx
    jlink.set_reset_pin_low()
    # Reset the JTAG TAP controller
    jtag.tap_reset()

    # Get the number of TAPs in the JTAG chain
    num_taps = jtag.get_num_taps()
    print(f'\nNumber of TAPs in JTAG chain: {num_taps}' )

    # Read and display the IDCODEs of all TAPs
    id_codes = jtag.get_tap_id_code(num_taps)
    print('Detected TAPs with IDCODEs:')
    for i, idcode in enumerate(id_codes):
        print(f'  TAP {i}: '
              f'IDCODE: 0x{idcode:08X}')


    # Configure IR and BSR lengths based on BSDL file
    jtag.set_ir_lengths([5, 4])
    jtag.set_bsr_lengths([bsdl.get_bsr_len(), 0])

    # Initialize boundary-scan register interface
    b = CBBsr(jtag, verbose=2)

    # Configure pins for boundary-scan operations
    led_pin_tout = CBRsrOutputToggler(bsdl, 'PA5', toggle_time = 0.5)
    led_pin_in = CBBsrPinNotifier(bsdl, 'PA5',  cb=pin_changed_cb)
    btn_pin_in = CBBsrPinNotifier(bsdl, 'PC13', cb=pin_changed_cb)

    b.add_pin(led_pin_tout)
    b.add_pin(led_pin_in)
    b.add_pin(btn_pin_in)

    # Finally, configure and start the boundary-scan operations
    b.config_pins()
    b.start()

    k = KeyStroke()
    print('\nStarting boundary-scan operations')
    print('Press ESC to terminate!')
    while True:
        # check whether a key from the list has been pressed
        if k.check(['\x1b', 'q', 'x']):
            break
        time.sleep(0.1)

    # Gracefully stop boundary-scan operations and clean up
    b.stop()
    b.deconfig_pins()
    jlink.set_reset_pin_high()
    jtag.close()



# Run the main function if this script is executed
if __name__ == '__main__':
    main()

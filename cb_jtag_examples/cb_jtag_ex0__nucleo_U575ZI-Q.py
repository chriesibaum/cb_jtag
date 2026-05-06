#!/usr/bin/env python3

# cb_jtag demo for the NUCLEO-U575ZI-Q board

import time
from cb_jtag import CBJtag
from cb_jtag import CBJLink
from cb_jtag import CBBsr
from cb_jtag import CBBsrPinNotifier
from cb_jtag import CBRsrOutput
from cb_jtag import CBRsrOutputToggler
from cb_bsdl_parser import CBBsdl
from key_stroke import *


bsdl_file = './bsdl_files/STM32U575_U585_LQFP144.bsd'


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
    b = CBBsr(jtag, verbose=1)

    # Configure pins for boundary-scan operations
    led1_pin_tout = CBRsrOutputToggler(bsdl, 'PC7', toggle_time=2.5,
                                       verbose=True)
    led1_pin_in = CBBsrPinNotifier(bsdl, 'PC7', cb=pin_changed_cb)
    b.add_pin(led1_pin_tout)
    b.add_pin(led1_pin_in)

    led2_pin_out = CBRsrOutput(bsdl, 'PB7', val=0, verbose=False)
    b.add_pin(led2_pin_out)

    led3_pin_out = CBRsrOutputToggler(bsdl, 'PG2', toggle_time=0.1)
    b.add_pin(led3_pin_out)

    user_btn_pin_in = CBBsrPinNotifier(bsdl, 'PC13', cb=pin_changed_cb)
    b.add_pin(user_btn_pin_in)


    # Finally, configure and start the boundary-scan operations
    b.config_pins()
    b.start()

    led2_bit = 0
    k = KeyStroke()
    print('\nStarting boundary-scan operations')
    print('Press ESC to terminate!')
    while True:
        led2_bit ^= 1
        led2_pin_out.set_bit(led2_bit)

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
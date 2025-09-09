#!/usr/bin/env python3

# NUCLEO-G474RE
# STM32G474RE

import time
import cb_jtag
from cb_jtag import CBJLink
from cb_jtag import CBBsr
from cb_jtag import CBBsrPinNotifier
from cb_jtag import CBRsrOutput
from cb_jtag import CBRsrOutputToggler
from cb_bsdl_parser import CBBsdl

from key_stroke import *

bsdl_file = './bsdl_files/lpc1857fet256_revA_20180227-v1.bsd'


def pin_changed_cb(pin, val):
    print(f'Pin {pin} changed to {val}')


if __name__ == '__main__':
    bsdl = CBBsdl(bsdl_file)

    jlink = CBJLink()

    emulators = jlink.connected_emulators()

    # Print the serial number of all emulators
    for emu in emulators:
        print(f'S/N: {emu.SerialNumber}')

    # Get the first emulator S/N to connect to it
    if not emulators:
        print("No J-Link emulators found.")
        exit(1)
    serial_no = emulators[0].SerialNumber

    # Open a connection to your J-Link.
    jlink.open(serial_no)
    jlink.set_speed(10000)
    jlink.set_tif(cb_jtag.enums.JLinkInterfaces.JTAG)


    jtag = cb_jtag.CBJtag(jtag_iface=jlink)


    # jlink.set_reset_pin_low()       # hold the reset pin low for STM32xxx
    jtag.tap_reset()

    num_taps = jtag.get_num_taps()
    print(f'Number of TAPs in chain: {num_taps}' )

    id_codes = jtag.get_tap_id_code(num_taps)
    for i, idcode in enumerate(id_codes):
        print(f"TAP {i}: ", end="")
        print(f"IDCODE: 0x{idcode:08X}")

    jtag.get_tap_id_code(num_taps)

    jtag.set_ir_lengths([5])
    jtag.set_bsr_lengths([bsdl.get_bsr_len()])

    # set the TAP to SAMPLE and read the BS register
    # jtag.instr(0, 0b00000)
    # bs_init = jtag.read_dr(545)

    # print(f'bs_write:       0x{bs_init:076x}')

    b = CBBsr(jtag, verbose=False)

    # led_pin_tout = CBRsrOutputToggler(bsdl, 'PA5', toggle_time = 0.5, ctrl_value = 0)
    # led_pin_in = CBBsrPinNotifier(bsdl, 'PA5', pin_changed_cb)
    # btn_pin_in = CBBsrPinNotifier(bsdl, 'PC13', pin_changed_cb)

    # led_pin_out = CBRsrOutput(bsdl, 'PA5', value=1)

    # b.add_pin(led_pin_tout)
    # b.add_pin(led_pin_out)
    # b.add_pin(led_pin_in)
    # b.add_pin(btn_pin_in)

    pin_pd13_in = CBBsrPinNotifier(bsdl, 'PD_13', pin_changed_cb)
    b.add_pin(pin_pd13_in)

    b.config_pins()

    b.start()


    k = KeyStroke()
    print('Press ESC to terminate!')
    while True:
        # led_pin_out.value ^= 1

        # check whether a key from the list has been pressed
        if k.check(['\x1b', 'q', 'x']):
            break

        # print()
        time.sleep(0.1)


    b.stop()
    jtag.close()

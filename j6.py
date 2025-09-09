#!/usr/bin/env python3

# NUCLEO-G474RE
# STM32G474RE

import time
import cb_jtag
from cb_jtag import CBJLink
from cb_bsdl_parser import CBBsdl
from key_stroke import *

bsdl_file = './bsdl_files/STM32G471_473_474_483_484_LQFP64.bsdl'
#bsdl_file = './bsdl_files/STM32G431_441_LQFP64.bsd'

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


    print('run...')
    # hold the reset pin low

    jtag.tap_reset()
    jlink.set_reset_pin_low()

    num_taps = jtag.get_num_taps()
    print(f'Number of TAPs in chain: {num_taps}' )

    id_codes = jtag.get_tap_id_code(num_taps)
    for i, idcode in enumerate(id_codes):
        print(f"TAP {i}: ", end="")
        print(f"IDCODE: 0x{idcode:08X}")


    jtag.set_ir_lengths([5, 4])
    jtag.set_bsr_lengths([bsdl.get_bsr_len(), 0])


    k = KeyStroke()
    print('Press ESC to terminate!')


    # read the BSR with instr SAMPLE = opcode 0b00010
    bsr_init = jtag.read_bsr(0, 0b00010)

    bsr_wr = bsr_init

    # set PA5 to output
    led_pin = 'PA5'
    led_ctrl_cell = bsdl.get_bsr_ctrl_cell(led_pin+'_out')
    led_data_cell = bsdl.get_bsr_data_cell(led_pin+'_out')

    btn_pin = 'PC13'
    btn_data_cell = bsdl.get_bsr_data_cell(btn_pin+'_in')

    bsr_wr = bsr_wr.clear_bit(led_ctrl_cell)

    while True:
        bsr_wr = bsr_wr.toggle_bit(led_data_cell)

        print(f'bs_write:       0x{bsr_wr:076x}')


        bsr_rd = jtag.write_bsr(0, 0b00000, bsr_wr)

        # read user button PC13
        btn = bsr_rd.get_bit(btn_data_cell)

        print(f"bs read:        0x{bsr_rd:076X}, btn: {btn}")

        # check whether a key from the list has been pressed
        if k.check(['\x1b', 'q', 'x']):
            break

        print()
        time.sleep(0.5)

    print('do finito')


    jtag.close()

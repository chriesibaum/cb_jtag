#!/usr/bin/env python3

import time
import cb_jtag
from key_stroke import *


if __name__ == '__main__':
    # serial_no = '600106950'
    jlink = cb_jtag.CBJLink()

    emulators = jlink.connected_emulators()

    # Print the serial number of all emulators
    for emu in emulators:
        print(f'S/N: {emu.SerialNumber}')

    # Get the first emulator S/N
    serial_no = emulators[0].SerialNumber

    # Open a connection to your J-Link.
    jlink.open(serial_no)
    jlink.set_speed(1000)
    jlink.set_tif(cb_jtag.enums.JLinkInterfaces.JTAG)


    jtag = cb_jtag.CBJtag(jtag_iface=jlink)


    print('run...')

    # hold the reset pin low
    jlink.set_reset_pin_low()

    jtag.tap_reset()

    num_taps = jtag.get_num_taps()
    print(f'Number of TAPs in chain: {num_taps}' )

    id_codes = jtag.get_tap_id_code(num_taps)
    for i, idcode in enumerate(id_codes):
        print(f"TAP {i}: ", end="")
        print(f"IDCODE: 0x{idcode:08X}")

    # total_ir_length = jtag.get_total_ir_len()
    # print(f"Total IR length: {total_ir_length} bits")


    jtag.set_ir_lengths([5, 4])

    jtag.set_bsr_lengths([240, 0])


    k = KeyStroke()
    print('Press ESC to terminate!')


    # read the BSR with instr SAMPLE = opcode 0b00010
    bsr_init = jtag.read_bsr(0, 0b00010)
    print(f"bs read:        0x{bsr_init:076X}")

    bsr_wr = bsr_init

    # set PA5 to output
    bsr_wr = bsr_wr.clear_bit(173)

    while True:
        bsr_wr = bsr_wr.toggle_bit(172)

        print(f'bs_write:       0x{bsr_wr:076x}')


        bsr_rd = jtag.write_bsr(0, 0b00000, bsr_wr)

        btn = bsr_rd.get_bit(222)

        print(f"bs read:        0x{bsr_rd:076X}, btn: {btn}")

        # check whether a key from the list has been pressed
        if k.check(['\x1b', 'q', 'x']):
            break

        print()
        time.sleep(0.5)

    print('do finito')

    jlink.set_reset_pin_high()
    jtag.close()
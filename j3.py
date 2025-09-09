#!/usr/bin/env python3

import time
import cb_jtag
from key_stroke import *

from pylink import library

if __name__ == '__main__':
    # serial_no = '600106950'

    # with specify the path to your J-Link library
    # lib = library.Library(dllpath='./libjlinkarm.so.8.10.6')
    # jlink = cb_jtag.CBJLink(lib=lib)

    # or use the default J-Link library from the system
    jlink = cb_jtag.CBJLink()


    emulators = jlink.connected_emulators()

    # Print the serial number of all emulators
    for emu in emulators:
        print(f'S/N: {emu.SerialNumber}')

    # Get the first emulator S/N
    serial_no = emulators[0].SerialNumber

    # Open a connection to your J-Link.
    jlink.open(serial_no)
    jlink.set_speed(10000)
    jlink.disable_dialog_boxes()

    # jlink.set_tif(cb_jtag.enums.JLinkInterfaces.JTAG)

    # Connect to the target device.
    # target = 'LPC1837'
    target = 'STM32g474re'
    # target = 'STM32U575zi'
    # target = 'STM32F746ZG'
    target = ''
    # jlink.connect(target, verbose=True)

    jtag = cb_jtag.CBJtag(jtag_iface=jlink)

    # import sys
    # sys.exit(-1)  # Exit early for testing purposes

    print('run...')

    # hold the reset pin low
    # jlink.set_reset_pin_low()

    jtag.tap_reset()


    jtag.get_tap_id_code()

    num_taps = jtag.get_num_taps()
    print(f'number of TAPs: {num_taps}' )

    jtag.get_tap_id_code(num_taps)


    # total_ir_length = jtag.get_total_ir_len()
    # print(f"Total IR length: {total_ir_length} bits")


    jtag.set_ir_lengths([5])

    jtag.tap_reset()


    k = KeyStroke()
    print('Press ESC to terminate!')


    # set the TAP to SAMPLE and read the BS register
    jtag.instr(0, 0b00000)
    bs_init = jtag.read_dr(545)

    bs_wr = bs_init

    # set PA5 to output
    bs_wr = bs_wr.clear_bit(353)

    while True:
        bs_wr = bs_wr.toggle_bit(354)

        print(f'bs_write:       0x{bs_wr:076x}')


        # set the TAP to EXTEST
        jtag.instr(0, 0b00000)
        bs_rd = jtag.write_dr(545, bs_wr)


        bit_287_ctrl = bs_rd.get_bit(287)
        bit_286_out3 = bs_rd.get_bit(286)
        bit_285_in = bs_rd.get_bit(285)


        print(f"bs read:        0x{bs_rd:076X}, bit_287_ctrl = {bit_287_ctrl}, bit_286_out3 = {bit_286_out3}, bit_285_in = {bit_285_in}, output: bit_220 = {bs_rd >> (220) & 0x01}")

        # check whether a key from the list has been pressed
        if k.check(['\x1b', 'q', 'x']):
            break

        print()
        time.sleep(0.5)

    print('do finito')

    # # Do whatever you want from here on in.
    # # jlink.flash(firmware, 0x0)
    # jlink.reset()

    # jlink.reset()
    jtag.close()
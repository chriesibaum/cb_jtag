#!/usr/bin/env python3

from cb_jtag.cb_jtag_probe import CBJtagProbe

jtag = CBJtagProbe()

# # Get firmware version
# fw_version = jtag.get_fw_version()
# print(f'Firmware Version: {fw_version}')

# set_freq = 15625000  # 1 kHz
# print(f'JTAG clock frequency set to {set_freq} Hz')
# jtag.set_freq(set_freq)

# Prepare buffers
tdi = bytearray([0xFF, 0x00])
tms = bytearray([0x00, 0x00])
tdo = bytearray(2)



# Transfer 16 bits
jtag.jtag_write_read(tdi, tdo, tms, 16)

print(f"TDO Received: {tdo.hex()}")
jtag.close()

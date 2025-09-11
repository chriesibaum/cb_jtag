
import math
import ctypes
import time
from .cb_jtag_iface_base import CBJtagIfaceBase
from .cb_jtag_fsm import Tap_FSM_State
from .cb_bit import CBBit


MAX_TAPS_IN_CHAIN = 128 # maximum number of TAP's in a JTAG chain


class CBJtagError(Exception):
    """Base class for exceptions in this module."""
    pass


class CBJtag():
    """Class to handle JTAG operations using a interface such as J-Link.
    This class provides methods to control the JTAG TAP state machine, set instruction lengths,
    reset the TAP, and perform JTAG operations like reading and writing data."""

    def __init__(self, jtag_iface, verbose=False):
        """Initialize the JTAG interface.
        Args:
            jtag_iface (CBJtagIfaceBase): An instance of a JTAG interface class
                (e.g., CBJLink) that implements the CBJtagIfaceBase interface.
        Raises:
            CBJtagError: If the JTAG interface is not properly initialized.
        """

        self.jtag_iface = None

        if not isinstance(jtag_iface, CBJtagIfaceBase):
            raise CBJtagError("Invalid JTAG interface provided. Must be an instance of CBJtagIfaceBase.")

        self.verbose = verbose

        self.jtag_iface = jtag_iface

        self.num_taps = None

        self.ir_lengths = []
        self.total_ir_len = None

        # ensure the JTAG interface is flushed and empty
        self.jtag_iface.jtag_flush()
        # self.jtag_iface.sys_reset()   -> rest not available from J-Link!!!

        # Reset the TAP state machine to the "Test Logic Reset" state
        # since we have no TRST pin this is the only way to reset the TAP
        self.tap_reset()

        self.tap_fsm = Tap_FSM_State.NONE

    def __del__(self):
        """Destructor to ensure the JTAG interface is closed."""
        self.close()

    def close(self):
        """Close the JTAG interface."""
        if self.jtag_iface is not None:
            self.jtag_iface.close()

    def set_verbose(self, verbose):
        """Set the verbosity level for debugging output.
        Args:
            verbose (bool): If True, enable verbose output; otherwise, disable it.
        """
        self.verbose = verbose

    def tap_reset(self):
        """Reset the TAP state machine to the "Test Logic Reset" state."""

        n_bits = 5
        tms_buf = bytes([0b11111])
        tdi_buf = bytes([0b00000])
        tdo_buf = (ctypes.c_ubyte * 1)()

        self.jtag_iface.jtag_write_read(tdi_buf,
                                        tdo_buf,
                                        tms_buf,
                                        n_bits)

        self.tap_fsm = Tap_FSM_State.TEST_LOGIC_RESET



    def tap_goto_sel_shift_dr(self):
        # tap fsm: from reset go to state shift_dr

        if self.tap_fsm != Tap_FSM_State.RUN_TEST_IDLE:
            self.tap_reset()

            n_bits = 4
            tms_buf = bytes([0b0010])
            tdi_buf = bytes([0b0000])
        else:   # pragma: no cover - todo: add some test
            n_bits = 3
            tms_buf = bytes([0b001])
            tdi_buf = bytes([0b000])

        tdo_buf = (ctypes.c_ubyte * 1)()

        self.jtag_iface.jtag_write_read(tdi_buf,
                                        tdo_buf,
                                        tms_buf,
                                        n_bits)

    def tap_goto_shift_ir(self):
        # tap fsm: from reset go to state shift-ir

        if self.tap_fsm != Tap_FSM_State.RUN_TEST_IDLE:
            self.tap_reset()
            n_bits = 5
            tms_buf = bytes([0b00110])
            tdi_buf = bytes([0b00000])
        else:
            n_bits = 4
            tms_buf = bytes([0b0011])
            tdi_buf = bytes([0b0000])

        tdo_buf = (ctypes.c_ubyte * 1)()

        # send the command to the J-Link
        self.jtag_iface.jtag_write_read(tdi_buf,
                                        tdo_buf,
                                        tms_buf,
                                        n_bits)


    def tap_go(self, tms, n_bits = 0, tap_fsm=Tap_FSM_State.NONE):
        # tap fsm: go from actual pos to x

        tms_buf = bytes([tms])
        tdi_buf = bytes([0x00])
        tdo_buf = (ctypes.c_ubyte * 1)()

        # print(f'tms @ tap_go: {tms_buf}')

        self.jtag_iface.jtag_write_read(tdi_buf,
                                        tdo_buf,
                                        tms_buf,
                                        n_bits)

        self.tap_fsm = tap_fsm



    def get_num_taps(self):
        self.tap_goto_shift_ir()

        # clk in 1 to set all TAP's into bypass mode
        num_bytes = 128
        tms_buf = bytes([0x00] * num_bytes)
        tdi_buf = bytes([0xff] * num_bytes)
        tdo_buf = (ctypes.c_ubyte * num_bytes)()
        n_bits = len(tms_buf) * 8

        self.jtag_iface.jtag_write_read(tdi_buf,
                                        tdo_buf,
                                        tms_buf,
                                        n_bits)


        # to go to Exit1-IR
        tms_buf = bytes([0b1])
        tdi_buf = bytes([0b1])
        tdo_buf = (ctypes.c_ubyte * 1)()
        n_bits = 1

        self.jtag_iface.jtag_write_read(tdi_buf,
                                        tdo_buf,
                                        tms_buf,
                                        n_bits)


        # now we are in Exit1-IR, go to Shift-DR
        n_bits = 4
        tms_buf = bytes([0b0011])
        tdi_buf = bytes([0b0000])
        tdo_buf = (ctypes.c_ubyte * 1)()

        self.jtag_iface.jtag_write_read(tdi_buf,
                                        tdo_buf,
                                        tms_buf,
                                        n_bits)

        # clk in "0" to flush the DR
        num_bytes = 128
        tms_buf = bytes([0x00] * num_bytes)
        tdi_buf = bytes([0x00] * num_bytes)
        tdo_buf = (ctypes.c_ubyte * num_bytes)()
        n_bits = len(tms_buf)

        self.jtag_iface.jtag_write_read(tdi_buf,
                                        tdo_buf,
                                        tms_buf,
                                        n_bits)

        # clk in 1 and read it back until we get the first 1
        # the ammount of CLK's correspondes to the number of of TAP's
        n_bits = 1
        tms_buf = bytes([0b0])
        tdi_buf = bytes([0b1])
        tdo_buf = (ctypes.c_ubyte * 1)()

        i = 0
        while True:
            self.jtag_iface.jtag_write_read(tdi_buf,
                                            tdo_buf,
                                            tms_buf,
                                            n_bits)

            x = int.from_bytes(bytearray(tdo_buf), 'little')

            if x == 1:
                self.num_taps = i
                return(self.num_taps)

            if i > MAX_TAPS_IN_CHAIN:       # pragma: no cover
                self.num_taps = 0
                raise CBJtagError(f"Too many TAPs in chain detected (> {MAX_TAPS_IN_CHAIN}) - aborting")
            i += 1

    def set_ir_lengths(self, ir_lengths):
        """Set the IR lengths for each TAP in the JTAG chain.
        Args:
            ir_lengths (list): A list of IR lengths for each TAP.
        Raises:
            CBJtagError: If the total IR length does not match the expected value.
        """

        calc_ir_len = sum(ir_lengths)

        # # check the actual ir length
        # if self.total_ir_len is not set, retrieve it
        if self.total_ir_len == None:
            self.total_ir_len = self.get_total_ir_len()

        if self.total_ir_len != calc_ir_len:    # pragma: no cover - todo: add some test
            raise CBJtagError(f"IR length mismatch: expected {calc_ir_len}, got {self.total_ir_len}")

        self.ir_lengths = ir_lengths

    def get_total_ir_len(self):
        """Detect the total length of the Instruction Register (IR) chain.

        This method automatically detects the total IR length by:
        1. Resetting TAPs and going to Shift-IR state
        2. Filling the IR with all 1s (bypass mode)
        3. Shifting in 0s and counting until a 0 appears at TDO

        Returns:
            int: The total length of the IR chain in bits.
        """
        # Reset TAPs and go to Shift-IR state
        self.tap_goto_shift_ir()

        # First, fill the entire IR chain with 1s (this puts all TAPs in bypass mode)
        # We use a generous number to ensure we fill the entire chain
        max_ir_length = 512  # Should be more than enough for most chains

        n_bits = max_ir_length
        n_bytes = math.ceil(n_bits / 8)
        tms_buf = bytes([0x00] * n_bytes)  # Keep TMS low to stay in Shift-IR
        tdi_buf = bytes([0xFF] * n_bytes)  # Fill with all 1s
        tdo_buf = (ctypes.c_ubyte * n_bytes)()

        self.jtag_iface.jtag_write_read(tdi_buf, tdo_buf, tms_buf, n_bits)

        # Now shift in 0s one bit at a time and count until we see a 0 at TDO
        # The number of shifts needed equals the total IR length
        n_bits = 1
        tms_buf = bytes([0x00])  # Keep TMS low to stay in Shift-IR
        tdi_buf = bytes([0x00])  # Shift in 0s
        tdo_buf = (ctypes.c_ubyte * 1)()

        ir_length = 0
        max_attempts = 512  # Safety limit

        for i in range(max_attempts):
            self.jtag_iface.jtag_write_read(tdi_buf, tdo_buf, tms_buf, n_bits)

            # Check if we got a 0 at TDO (the first 1 we shifted in earlier)
            tdo_bit = int.from_bytes(bytearray(tdo_buf), 'little') & 1

            if tdo_bit == 0:
                ir_length = i   # + 1 todo: check if +1 is needed
                break

        if ir_length == 0:    # pragma: no cover - todo: add some test
            raise CBJtagError("Could not detect IR length - no TAPs found or IR length > 512 bits")

        # Exit Shift-IR and go to Run-Test/Idle
        self.tap_go(0b011, 3, Tap_FSM_State.RUN_TEST_IDLE)

        self.total_ir_len = ir_length
        return self.total_ir_len

    def set_bsr_lengths(self, bsr_lengths):
        """Set the BSR lengths for each TAP in the JTAG chain.
        Args:
            bsr_lengths (list): A list of BSR lengths for each TAP.
        """

        self.bsr_lengths = bsr_lengths

    def get_tap_id_code(self, num_taps=1):
        self.tap_goto_sel_shift_dr()

        n_bits = 32
        tdi_buf = bytes([0x00, 0x00, 0x00, 0x00])
        tms_buf = bytes([0x00, 0x00, 0x00, 0x00])

        num_bytes = 4
        tdo_buf = (ctypes.c_ubyte * num_bytes)()

        self.idcodes = []
        for i in range(num_taps):

            self.jtag_iface.jtag_write_read(tdi_buf,
                                            tdo_buf,
                                            tms_buf,
                                            n_bits)

            idcode = int.from_bytes(bytearray(tdo_buf), 'little')
            self.idcodes.append(idcode)

        return self.idcodes

    def instr(self, tap_num, opcode):
        """Sends an instruction to the specified TAP.

        Args:
            tap_num (int): the index of the TAP to send the instruction to.
            opcode (int): the instruction to send.

        Returns:
            ``None``

        Raises:
            JLinkException: on error.
        """
        if tap_num >= self.num_taps:    # pragma: no cover - todo: add some test
            raise CBJtagError('Invalid TAP number')


        self.tap_goto_shift_ir()

        # fill the tdi with 1 to set unused TAP's into bypass mode
        tdi = 0
        tdi = (1 << self.total_ir_len) -1

        opcode_pos = self.total_ir_len - sum(self.ir_lengths[:tap_num+1])

        for i in range(self.ir_lengths[tap_num]):
            bit = (opcode >> i) & 1
            if bit:
                tdi |=  (1 << (i+opcode_pos))
            else:
                tdi &= ~(1 << (i+opcode_pos))

        # set last bit "1" to set TAP finaly to Eixit1-IR
        tms = 1 << (self.total_ir_len - 1)

        if self.verbose:
            print(f'tdi: 0b{tdi:0{self.total_ir_len}b}, tms: {tms:0{self.total_ir_len}b}')

        n_bits = self.total_ir_len
        n_bytes = math.ceil(self.total_ir_len / 8)
        tms_buf = tms.to_bytes(n_bytes, byteorder='little')
        tdi_buf = tdi.to_bytes(n_bytes, byteorder='little')
        tdo_buf = (ctypes.c_ubyte * n_bytes)()

        self.jtag_iface.jtag_write_read(tdi_buf,
                                        tdo_buf,
                                        tms_buf,
                                        n_bits)

        # go to RUN-Test/Idle state
        self.tap_go(0b01, 2, Tap_FSM_State.RUN_TEST_IDLE)


    def read_dr(self, bit_len):
        """Reads the data register (DR) of the JTAG TAP.
        Args:
            bit_len (int): The number of bits to read from the DR.
        Returns:
            int: The value read from the DR.
        Raises:
            CBJtagError: If the bit length is invalid or if the TAP is not
            in the correct state.
        """
        # got to Shift DR
        self.tap_go(0b001, 3, Tap_FSM_State.SHIFT_DR)

        n_bits = bit_len
        n_bytes = math.ceil(n_bits / 8)
        tms_buf = bytes([0x00] * n_bytes)
        tdi_buf = bytes([0x00] * n_bytes)
        tdo_buf = (ctypes.c_ubyte * n_bytes)()

        # tdi = 0x920000024924124924924900000000000924900000024000124924124000004000124900
        # tdi_buf = tdi.to_bytes(n_bytes, byteorder='little')

        self.jtag_iface.jtag_write_read(tdi_buf,
                                        tdo_buf,
                                        tms_buf,
                                        n_bits)

        # print(f'len: {len(tdo_buf)}')

        boundary_scan = int.from_bytes(bytearray(tdo_buf), 'little') >> (self.num_taps -1)
        boundary_scan = CBBit(boundary_scan)

        # go to RUN-Test/Idle state
        self.tap_go(0b011, 3, Tap_FSM_State.RUN_TEST_IDLE)

        return boundary_scan


    def write_dr(self, n_bits, dr):
        """Reads the data register (DR) of the JTAG TAP.
        Args:
            n_bits (int): The number of bits to read from the DR.
            dr (int): The value to write to the DR.
        Returns:
            int: The value read from the DR.
        Raises:
            CBJtagError: If the bit length is invalid or if the TAP is not
            in the correct state.
        """
        # got to Shift DR
        self.tap_go(0b001, 3, Tap_FSM_State.SHIFT_DR)

        n_bytes = math.ceil(n_bits / 8)

        # go to Exit1-DR at the end
        tms = 1 << (n_bits - 1)
        if self.verbose:
            print(f'tms:           0x{tms:0{n_bytes}x}')

        # prepare and load the buffers
        tms_buf = tms.to_bytes(n_bytes, byteorder='little')
        tdi_buf = dr.to_bytes(n_bytes, byteorder='little')
        tdo_buf = (ctypes.c_ubyte * n_bytes)()

        # clk data into the DR
        self.jtag_iface.jtag_write_read(tdi_buf,
                                        tdo_buf,
                                        tms_buf,
                                        n_bits)


        boundary_scan = int.from_bytes(bytearray(tdo_buf), 'little') >> (self.num_taps -1)
        boundary_scan = CBBit(boundary_scan)

        # go to RUN-Test/Idle state
        self.tap_go(0b01, 2, Tap_FSM_State.RUN_TEST_IDLE)

        return boundary_scan


    def read_bsr(self, tap_num, opcode):
        """Reads the boundary scan register (BSR) of the JTAG TAP.
        """

        # set the TAP to OPCODE and read the BS register
        self.instr(tap_num, opcode)
        bsr = self.read_dr(self.bsr_lengths[tap_num])

        return bsr

    def write_bsr(self, tap_num, opcode, bsr):
        """Writes to the boundary scan register (BSR) of the JTAG TAP.
        """

        # set the TAP to OPCODE and write the BS register
        self.instr(tap_num, opcode)
        bsr = self.write_dr(self.bsr_lengths[tap_num], bsr)

        return bsr
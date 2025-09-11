

from cb_jtag.cb_bit import CBBit


class Test_CBBit:

    @classmethod
    def setup_class(self):
        self.val = 0
        self.bit = CBBit(self.val)


    def test_000_cb_bit(self):
        assert self.bit is not None, "CBBit instance is None"
        assert isinstance(self.bit, CBBit), "CBBit instance is not of type CBBit"


    def test_010_set_get(self):
        print('Testing CBBit set and get methods')
        bit_pos = 0

        # Initial value should be 0
        assert self.bit.get_bit(bit_pos) == 0, "Initial CBBit value is not 0"

        # Set to 1 and verify
        self.bit = self.bit.set_bit(bit_pos, 1)
        assert self.bit.get_bit(bit_pos) == 1, "CBBit value after set() is not 1"

        # Clear to 0 and verify
        self.bit = self.bit.clear_bit(bit_pos)
        assert self.bit.get_bit(bit_pos) == 0, "CBBit value after clear() is not 0"

        # Set to 1 and verify
        self.bit = self.bit.set_bit(bit_pos)
        assert self.bit.get_bit(bit_pos) == 1, "CBBit value after set() is not 1"

        # Set to 0 and verify
        self.bit = self.bit.set_bit(bit_pos, 0)
        assert self.bit.get_bit(bit_pos) == 0, "CBBit value after set() is not 0"


    def test_020_toggle(self):
        print('Testing CBBit toggle method')
        bit_pos = 0
        self.bit = self.bit.clear_bit(bit_pos)

        # Toggle to 1 and verify
        self.bit = self.bit.toggle_bit(bit_pos)
        assert self.bit.get_bit(bit_pos) == 1, "CBBit value after toggle() is not 1"

        # Toggle back to 0 and verify
        self.bit = self.bit.toggle_bit(bit_pos)
        assert self.bit.get_bit(bit_pos) == 0, "CBBit value after second toggle() is not 0"
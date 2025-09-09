class CBBit(int):
    """A class to do bit operations for JTAG boundary scan.
    This class extends the built-in int type to provide a more
    meaningful representation of a single bit in JTAG operations.
    It can be used to manipulate bits in a JTAG data stream."""


    def get_bit(self, bit_pos):
        """Get the value of a specific bit position.
        Args:
            bit_pos (int): The position of the bit to retrieve (0-indexed).
        Returns:
            int: The value of the specified bit (0 or 1).
        """
        return (self >> bit_pos) & 1

    def set_bit(self, bit_pos, value = None):
        """Set the value of a specific bit position.
        Args:
            bit_pos (int): The position of the bit to set (0-indexed).
            value (int): The value to set (0 or 1).
        Returns:
            CBBit: A new CBBit instance with the updated value.
        """

        if value is None:
            # set the bit and return new CBBit instance
            return CBBit(self | (1 << bit_pos))
        else:
            if value:
                # set the bit and return new CBBit instance
                return CBBit(self | (1 << bit_pos))
            else:
                # clear the bit and return new CBBit instance
                return CBBit(self & ~(1 << bit_pos))

    def clear_bit(self, bit_pos):
        """Clear the value of a specific bit position.
        Args:
            bit_pos (int): The position of the bit to clear (0-indexed).
        Returns:
            CBBit: A new CBBit instance with the updated value.
        """
        # clear the bit and return new CBBit instance
        return CBBit(self & ~(1 << bit_pos))


    def toggle_bit(self, bit_pos):
        """Toggle the value of a specific bit position.
        Args:
            bit_pos (int): The position of the bit to toggle (0-indexed).
        Returns:
            CBBit: A new CBBit instance with the updated value.
        """
        # toggle the bit and return new CBBit instance
        return CBBit(self ^ (1 << bit_pos))

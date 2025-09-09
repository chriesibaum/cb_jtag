class CBJtagIfaceBase():
  def __init__(self):
     pass

  def jtag_write_read(self,
                      tdi_buf,
                      tdo_buf,
                      tms_buf,
                      n_bits):
      """Send TDI and TMS data to the JTAG interface and get TDO data back.

      Args:
        tdi_buf (bytes): The TDI data to send.
        tdo_buf (bytes): The buffer to store the TDO data.
        tms_buf (bytes): The TMS data to send.
        n_bits (int): The number of bits to transfer.

      Returns:
        int: The result of the operation.

      Raises:
        JLinkException: on error.
      """
      raise NotImplementedError("This method should be implemented by subclasses.")


  def close(self):
      """Close the JTAG interface."""
      raise NotImplementedError("This method should be implemented by subclasses.")

  # def set_sys_reset_pin_low(self):
  #     """Set the reset pin low."""
  #     raise NotImplementedError("This method should be implemented by subclasses.")

  # def set_sys_reset_pin_high(self):
  #     """Set the reset pin high."""
  #     raise NotImplementedError("This method should be implemented by subclasses.")

  # def sys_reset(self):
  #     """Reset the JTAG interface."""
  #     raise NotImplementedError("This method should be implemented by subclasses.")

  def jtag_flush(self):
      """Flush the JTAG interface."""
      raise NotImplementedError("This method should be implemented by subclasses.")


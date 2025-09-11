import pytest
from cb_jtag.cb_jtag_iface_base import CBJtagIfaceBase
from cb_jtag import CBJLink
from cb_jtag import CBJtag
from cb_jtag.cb_bsr import CBBsr

class Test_CBJtagIfaceBase:

    def test_000_instance(self):
        iface = CBJtagIfaceBase()
        assert iface is not None, "CBJtagIfaceBase instance is None"
        assert isinstance(iface, CBJtagIfaceBase), "CBJtagIfaceBase instance is not of type CBJtagIfaceBase"

    def test_010_methods(self):
        iface = CBJtagIfaceBase()

        with pytest.raises(NotImplementedError):
            iface.jtag_write_read(b'\x00', b'\x00', b'\x00', 8)

        with pytest.raises(NotImplementedError):
            iface.close()

        with pytest.raises(NotImplementedError):
            iface.jtag_flush()



class CBJtagDummyIface(CBJtagIfaceBase):
    def jtag_write_read(self, tdi_buf, tdo_buf, tms_buf, n_bits):
        return 0

    def close(self):
        pass

    def jtag_flush(self):
        pass


class Test_CBJtag:

    def test_000_instance(self):
        iface = CBJtagDummyIface()
        jtag = CBJtag(iface)
        assert jtag is not None, "CBJtag instance is None"
        assert isinstance(jtag, CBJtag), "CBJtag instance is not of type CBJtag"


    def test_010_invalid_iface(self):
        with pytest.raises(Exception):
            jtag = CBJtag(None)


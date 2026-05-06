import pytest
from cb_jtag.cb_jtag_probe_base import CBJtagProbeBase
from cb_jtag import CBJLink
from cb_jtag import CBJtag
from cb_jtag.cb_bsr import CBBsr

class Test_CBJtagProbeBase:

    def test_000_instance(self):
        iface = CBJtagProbeBase()
        assert iface is not None, "CBJtagProbeBase instance is None"
        assert isinstance(iface, CBJtagProbeBase), "CBJtagProbeBase instance is not of type CBJtagProbeBase"

    def test_010_methods(self):
        iface = CBJtagProbeBase()

        with pytest.raises(NotImplementedError):
            iface.jtag_write_read(b'\x00', b'\x00', b'\x00', 8)

        with pytest.raises(NotImplementedError):
            iface.close()

        with pytest.raises(NotImplementedError):
            iface.jtag_flush()



class CBJtagDummyIface(CBJtagProbeBase):
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


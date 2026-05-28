

from venv import logger

from cb_jtag.cb_jlink_probe import CBJLinkProbe
from cb_jtag.cb_jtag_probe import CBJtagProbe


class CBJtagProbeDiscover:
    def __init__(self):
        self.probe_drivers = [CBJtagProbe(), CBJLinkProbe()]

    def discover_probes(self):
        probes = {}
        for driver in self.probe_drivers:
            p = driver.get_probes()
            probes.update(p)

        return probes

    def get_probe(self, probe_id):
        probes = self.discover_probes()

        driver = probes[probe_id]['driver']

        if driver == 'CBJtagProbe':
            probe = CBJtagProbe()
        elif driver == 'CBJLinkProbe':
            probe = CBJLinkProbe()
        else:
            raise ValueError(f'Unknown driver {driver} for probe with id {probe_id}')

        probe.easy_setup_probe(probe_id=probe_id)

        return probe
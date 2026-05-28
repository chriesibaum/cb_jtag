import logging

from cb_jtag import CBJtag
from cb_jtag import CBJtagProbeDiscover
from cb_jtag import CBJtagProbe
from cb_jtag import CBJLinkProbe

logger = logging.getLogger(__name__)

def main():
    pd = CBJtagProbeDiscover()

    probes = pd.discover_probes()
    logger.info(f'Found {len(probes)} connected JTAG Probes:')


    for probe_id, probe_info in probes.items():
        logger.info(f"Probe ID: {probe_id}")
        logger.info(f"  Manufacturer: {probe_info['manufacturer']}")
        logger.info(f"  Product: {probe_info['product']}")
        logger.info(f"  Driver: {probe_info['driver']}")
        logger.info("")

    id = 'FA63A4D787703F31'
    id = '175104937'

    probe = pd.get_probe(id)

    jtag = CBJtag(jtag_probe=probe)

    logger.info(f'Probe Version: {jtag.get_probe_version()}')
    logger.info(f'Device ID: {jtag.get_probe_id_str()}')

    num_taps = jtag.get_taps_in_chain()
    logger.info(f'Number of TAPs in JTAG chain: {num_taps}')

    # Read and display the IDCODEs of all TAPs
    id_codes = jtag.get_tap_id_code(num_taps)
    logger.info('Detected TAPs with IDCODEs:')
    for i, idcode in enumerate(id_codes):
        logger.info(f'  TAP {i}: IDCODE: 0x{idcode:08X}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()

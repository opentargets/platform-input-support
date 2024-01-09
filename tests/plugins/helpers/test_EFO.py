from definitions import ROOT_DIR
from plugins.helpers.EFO import EFO


EFO_INPUT = ROOT_DIR + "/tests/resources/efo.jsonl"


def test_efo_get_prefix():
    efo = EFO(EFO_INPUT)
    # EFO term
    assert efo.get_prefix("EFO_123456") == "http://www.ebi.ac.uk/efo/"
    # OTAR term
    assert efo.get_prefix("OTAR_123456") == "http://www.ebi.ac.uk/efo/"
    # Orphanet term
    assert efo.get_prefix("Orphanet_123456") == "http://www.orpha.net/ORDO/"
    # default, unmatched
    assert efo.get_prefix("MONDO_123456") == "http://purl.obolibrary.org/obo/"

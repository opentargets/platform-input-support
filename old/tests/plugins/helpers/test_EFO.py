import os

import pytest

from platform_input_support import ROOT_DIR
from platform_input_support.modules.common.yaml_reader import YAMLReader
from platform_input_support.plugins.helpers.efo import EFO

EFO_INPUT = ROOT_DIR + '/tests/resources/efo.jsonl'


@pytest.fixture
def efo_conf():
    """Create the config."""
    yaml = YAMLReader(os.path.join(ROOT_DIR, 'config.yaml')).read_yaml()
    return yaml.steps.disease.etl.efo


def test_efo_get_prefix(efo_conf):
    efo = EFO(EFO_INPUT, efo_conf)
    # EFO term
    assert efo.get_prefix('EFO_123456') == 'http://www.ebi.ac.uk/efo/'
    # OTAR term
    assert efo.get_prefix('OTAR_123456') == 'http://www.ebi.ac.uk/efo/'
    # Orphanet term
    assert efo.get_prefix('Orphanet_123456') == 'http://www.orpha.net/ORDO/'
    # default, unmatched
    assert efo.get_prefix('OTHER_123456') == 'http://purl.obolibrary.org/obo/'

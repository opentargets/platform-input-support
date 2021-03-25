import unittest
from definitions import ROOT_DIR

from modules.helpers.HPO import HPO

class TestDiseaseStep(unittest.TestCase):
    """
    TBC: To be complete
    """

    def setUp(self):
        self.hpo_filename = ROOT_DIR+"/tests/resources/hp.jsonl"

    # exclude obsolete term
    def testHPO(self):
        HPOModule = HPO(self.hpo_filename)
        HPOModule.generate()
        assert len(HPOModule.hpo) == 4






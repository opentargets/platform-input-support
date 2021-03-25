import unittest
from definitions import ROOT_DIR
import subprocess

from modules.helpers.HPO import HPO
from modules.helpers.EFO import EFO
from modules.helpers.HPOPhenotypes import HPOPhenotypes

class TestDiseaseStep(unittest.TestCase):
    """
    TBC: To be complete
    """

    def setUp(self):
        self.hpo_filename = ROOT_DIR+"/tests/resources/hp.jsonl"
        self.efo_filename = ROOT_DIR+"/tests/resources/efo.jsonl"
        self.phenotype_filename = ROOT_DIR+"/tests/resources/phenotype.hpoa"


    def testDisease(self):
        EFOModule = EFO(self.efo_filename)
        process = subprocess.Popen("cat "+ self.efo_filename +"| grep -v deprecated | wc -l",
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   )
        num_valid_EFO = int(process.communicate()[0].decode("utf-8").replace("\n",""))
        EFOModule.generate()
        assert len(EFOModule.diseases) == num_valid_EFO

    # exclude obsolete term
    def testHPO(self):
        HPOModule = HPO(self.hpo_filename)
        process = subprocess.Popen("cat "+ self.hpo_filename +"| grep -v deprecated | wc -l",
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   )
        num_valid_HPO = int(process.communicate()[0].decode("utf-8").replace("\n", ""))
        HPOModule.generate()
        assert len(HPOModule.hpo) == num_valid_HPO

    def testHPOPhenotypes(self):
        HPModule = HPOPhenotypes(self.phenotype_filename)
        process = subprocess.Popen("cat "+ self.phenotype_filename +"| grep -v '#' | wc -l",
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   )
        num_valid_HP = int(process.communicate()[0].decode("utf-8").replace("\n", ""))
        outfile = HPModule.run('test_phenotype.jsonl')
        assert True == True




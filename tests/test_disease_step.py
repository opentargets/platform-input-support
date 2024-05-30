import subprocess
import unittest

from platform_input_support import ROOT_DIR
from platform_input_support.modules.common.yaml_reader import YAMLReader
from platform_input_support.plugins.helpers.efo import EFO
from platform_input_support.plugins.helpers.hpo import HPO
from platform_input_support.plugins.helpers.mondo import MONDO


class TestDiseaseStep(unittest.TestCase):
    """TBC: To be complete."""

    def setUp(self):
        self.hpo_filename = ROOT_DIR + '/tests/resources/hp.jsonl'
        self.efo_filename = ROOT_DIR + '/tests/resources/efo.jsonl'
        self.phenotype_filename = ROOT_DIR + '/tests/resources/phenotype.hpoa'
        self.mondo_filename = ROOT_DIR + '/tests/resources/mondo.jsonl'
        default_conf_file = ROOT_DIR + '/' + 'config.yaml'
        self.yaml_reader = YAMLReader(default_conf_file)
        self.config = self.yaml_reader.read_yaml()

    def test_disease(self):
        conf = self.config.disease.etl.efo
        efo_module = EFO(self.efo_filename, conf)
        process = subprocess.Popen(
            'cat ' + self.efo_filename + "| grep -v deprecated | grep -v 'Restric' | grep -v 'intersectionOf' | wc -l",
            shell=True,
            stdout=subprocess.PIPE,
        )
        num_valid_efo = int(process.communicate()[0].decode('utf-8').replace('\n', ''))
        efo_module.generate()
        assert len(efo_module.diseases) == num_valid_efo

    # exclude obsolete term
    def test_hpo(self):
        hpo_module = HPO(self.hpo_filename)
        process = subprocess.Popen(
            'cat ' + self.hpo_filename + '| grep -v deprecated | wc -l',
            shell=True,
            stdout=subprocess.PIPE,
        )
        num_valid_hpo = int(process.communicate()[0].decode('utf-8').replace('\n', ''))
        hpo_module.generate()
        assert len(hpo_module.hpo) == num_valid_hpo

    # def testHPOPhenotypes(self):
    #    HPModule = HPOPhenotypes(self.phenotype_filename)
    #    outfile = HPModule.run('test_phenotype.jsonl')
    #    assert (os.stat(outfile).st_size > 0) == True

    def test_mondo(self):
        mondo_module = MONDO(self.mondo_filename)
        process = subprocess.Popen(
            'cat ' + self.mondo_filename + '| grep -v deprecated | wc -l',
            shell=True,
            stdout=subprocess.PIPE,
        )
        num_valid_mondo = int(process.communicate()[0].decode('utf-8').replace('\n', ''))
        mondo_module.generate()
        assert len(mondo_module.mondo) == num_valid_mondo

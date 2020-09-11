import unittest
from modules.common.YAMLReader import YAMLReader


class TestYamlReader(unittest.TestCase):
    """
    YamlReader reads the 'config.yaml' file in the base directory and returning a dictionary representation.

    This test module includes basic validation tests (eg. 'test_config_parses'). Additional 'key specific' tests
    should be included here too as a validation mechanism (eg. chembl_indexes_have_fields).
    """

    def setUp(self):
        self.yaml_reader = YAMLReader()
        self.yaml_dict = self.yaml_reader.read_yaml()

    def test_config_parses(self):
        """
        Basic test to see if there are yaml parse errors: if the config file has a syntax problem an empty dictionary
        is returned.
        """
        self.assertGreater(len(self.yaml_dict), 0, "Yaml dict should not be empty.")

    def test_chembl_indexes_have_fields(self):
        """
        Checks that all listed ChEMBL elasticsearch indexes in config select at least one query field.
        """
        indexes = self.yaml_dict.ChEMBL.datasources.indices
        for i in indexes.values():
            for k, v in i.items():
                if k is 'fields':
                    self.assertGreater(len(v), 0, 'No fields provided on index {}'.format(k))
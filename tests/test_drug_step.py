import unittest
from mock import patch
from definitions import ROOT_DIR

import modules.Drug as Drug
from modules.common.YAMLReader import YAMLReader


class TestDrugStep(unittest.TestCase):
    """
    YamlReader reads the 'config.yaml' file in the base directory and returning a dictionary representation.
    """

    def setUp(self):
        default_conf_file = ROOT_DIR + '/' + 'config.yaml'
        self.yaml_reader = YAMLReader(default_conf_file)
        self.config = self.yaml_reader.read_yaml()

    @patch('modules.Drug.Drug._download_elasticsearch_data')
    def test_output_has_fields_to_write_to_GCP(self, mock1):
        """
        Step should return a dictionary with GCP target directory so that if `RetrieveResource` is configured to upload
        results it can save the files somewhere valid.
        """
        # Given
        # file names 'saved' by step
        es_return_values = ['f1', 'f2', 'f3']
        mock1.return_value = es_return_values
        # We only want to test the results of ES configuration at this point.
        es_config = self.config['drug']
        es_config.datasources.pop('downloads', None)
        # When
        drugStep = Drug.Drug(es_config)
        results = drugStep.get_all()
        # Then
            # Each file saved should be in returned dictionary
        self.assertEqual(len(results), len(es_return_values))
            # returned dictionary should have fields 'resource' and 'gs_output_dir'
        for f in es_return_values:
            self.assertTrue(f in results)
            self.assertTrue('resource' in results[f])
            self.assertTrue('gs_output_dir' in results[f])



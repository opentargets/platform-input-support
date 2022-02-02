import os
import yaml
import logging
from addict import Dict
from definitions import ROOT_DIR

logger = logging.getLogger(__name__)


class YAMLReader(object):

    def __init__(self, yaml_file):
        """
        Constructor

        :param yaml_file: path to YAML file to read from
        :return: a YAMLReader
        """
        self.yaml_file = yaml_file if yaml_file is not None else os.path.join(ROOT_DIR, 'config.yaml')
        self.yaml_dictionary = {}
        self.yaml_data = {}

    def read_yaml(self, standard_output=False):
        """
        Read the currently wrapped YAML file

        :param standard_output: whether the result should be text or a dictionary
        :return: text representation of yaml data if standard_output is set to True, a dictionary object otherwise
        """
        # print("Config file: " + self.yaml_file )
        with open(self.yaml_file, 'r') as stream:
            try:
                self.yaml_data = yaml.load(stream, yaml.SafeLoader)
                self.yaml_dictionary = Dict(self.yaml_data)
            except yaml.YAMLError as e:
                logger.error(f"The following ERROR occurred while reading YAML file '{self.yaml_file}', '{e}'")
        if standard_output:
            return self.yaml_data
        else:
            return self.yaml_dictionary

    def get_list_keys(self):
        """
        Get a listing of keys in the currently wrapped YAML file

        :return: a list of keys in the currently wrapped YAML file
        """
        return list(self.yaml_dictionary.keys())

import logging
import yaml
from addict import Dict
from definitions import ROOT_DIR

logger = logging.getLogger(__name__)


class YAMLReader(object):

    def __init__(self, yaml_file):
        self.yaml_file = yaml_file if yaml_file is not None else ROOT_DIR + '/' + 'config.yaml'
        self.yaml_dictionary = {}
        self.yaml_data = {}

    def get_yaml_data(self):
        return self.yaml_data

    def get_Dict(self):
        return self.yaml_dictionary

    def read_yaml(self, standard_output=False):
        # print("Config file: " + self.yaml_file )
        with open(self.yaml_file, 'r') as stream:
            try:
                self.yaml_data = yaml.load(stream, yaml.SafeLoader)
                self.yaml_dictionary = Dict(self.yaml_data)
            except yaml.YAMLError as exc:
                print(exc)
        yaml_output = self.yaml_dictionary if standard_output is False else self.yaml_data
        return yaml_output

    def get_list_keys(self):
        return list(self.yaml_dictionary.keys())

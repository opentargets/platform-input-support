import sys
from pathlib import Path

import yaml
from addict import Dict
from loguru import logger

from platform_input_support import ROOT_DIR


class YAMLReaderError(Exception):
    """YAML Reader Exception."""


class YAMLReader:
    """YAML reader."""

    def __init__(self, yaml_file: Path | None) -> None:
        """YAML Reader constructor.

        :param yaml_file: path to YAML file to read from or None
        """
        self._default_yaml_file = Path(ROOT_DIR).joinpath('config.yaml')
        self.yaml_file: Path = yaml_file if yaml_file is not None else self._default_yaml_file
        self.yaml_dict = Dict()

    def read_yaml(self) -> Dict:
        """Read the currently wrapped YAML file.

        :return: a dictionary object
        """
        logger.info(f'Reading config from {self.yaml_file}')
        with open(self.yaml_file, encoding='UTF-8') as stream:
            try:
                self.yaml_dict = Dict(yaml.load(stream, yaml.SafeLoader))
            except yaml.YAMLError:
                logger.critical('error reading config file')
                sys.exit(1)

        return self.yaml_dict

    def get_list_keys(self) -> list:
        """Get a listing of keys in the currently wrapped YAML file.

        :return: a list of keys in the currently wrapped YAML file
        """
        return list(self.yaml_dict.keys())

import logging
from pathlib import Path
from typing import Union
import yaml
from addict import Dict
from platform_input_support import ROOT_DIR

logger = logging.getLogger(__name__)


class YAMLReaderException(Exception):
    """YAML Reader Exception"""


class YAMLReader:
    """YAML reader"""

    def __init__(self, yaml_file: Union[Path, None]) -> None:
        """
        Constructor

        :param yaml_file: path to YAML file to read from or None
        """
        self._default_yaml_file = Path(ROOT_DIR).joinpath("config.yaml")
        self.yaml_file: Path = (yaml_file if yaml_file is not None
                                else self._default_yaml_file)
        self.yaml_dict = Dict()

    def read_yaml(self) -> Dict:
        """
        Read the currently wrapped YAML file

        :return: a dictionary object
        """
        logger.debug("Reading configuration file %s", self.yaml_file)
        with open(self.yaml_file, 'r', encoding="UTF-8") as stream:
            try:
                self.yaml_dict = Dict(yaml.load(stream, yaml.SafeLoader))
            except yaml.YAMLError as err:
                message = ("The following ERROR occurred while reading "
                           f"YAML file '{self.yaml_file}', '{err}'")
                logger.error(message)
                raise YAMLReaderException(message) from err
        return self.yaml_dict

    def get_list_keys(self) -> list:
        """
        Get a listing of keys in the currently wrapped YAML file

        :return: a list of keys in the currently wrapped YAML file
        """
        return list(self.yaml_dict.keys())

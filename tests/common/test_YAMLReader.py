import os
from pathlib import Path
import pytest
import yaml
from platform_input_support import ROOT_DIR

from platform_input_support.modules.common.YAMLReader import YAMLReader, YAMLReaderException


@pytest.fixture()
def yaml_config():
    """Create the test config"""
    # setup
    config_dict = {"a": "a",
                   "b": {"b1": "b1"},
                   "c": ["c1", "c2"],
                   "d": [{"d1": "d1"}, {"d2": "d2"}]}
    config_file = Path(ROOT_DIR).joinpath("tests/test_config.yaml")
    with open(config_file, "w", encoding="UTF-8") as f:
        yaml.dump(config_dict, f)
    yield config_file
    # teardown
    os.remove(config_file)


def test_yaml_reader(yaml_config):
    """Should not throw exceptions or errors"""
    yaml_reader = YAMLReader(yaml_config)
    assert yaml_reader.read_yaml()


def test_config_parses(yaml_config):
    """
    Basic test to see if there are yaml parse errors:
    if the config file has a syntax problem an empty dictionary
    is returned.
    """
    yaml_reader = YAMLReader(yaml_config)
    config_dict = yaml_reader.read_yaml()
    assert len(config_dict) > 0


def test_yaml_dict(yaml_config):
    """
    Checks that dict can be navigated
    """
    yaml_reader = YAMLReader(yaml_config)
    config_dict = yaml_reader.read_yaml()
    assert config_dict.a == "a"
    assert config_dict.b.b1 == "b1"
    assert len(config_dict.c) == 2
    assert config_dict.d[1].d2 == "d2"


def test_yaml_reader_throws_exception(yaml_config):
    """Should throw exception"""
    # invalidate yaml file
    with open(yaml_config, "a", encoding="UTF-8") as f:
        f.write("'")
    yaml_reader = YAMLReader(yaml_config)
    with pytest.raises(YAMLReaderException):
        yaml_reader.read_yaml()

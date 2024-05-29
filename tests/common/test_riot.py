from pathlib import Path
import shutil

import pytest

from platform_input_support import ROOT_DIR
from platform_input_support.modules.common.Riot import Riot, RiotException
from platform_input_support.modules.common.YAMLReader import YAMLReader


@pytest.fixture()
def riot_inputs():
    """Create the test config"""
    # setup
    test_dir = Path(ROOT_DIR) / 'tests' / 'riot_test_temp'
    yaml = YAMLReader(None).read_yaml()
    yaml.config.output_dir = test_dir
    yaml.config.java_vm = "-Xms1024m -Xmx1024m"
    Path(test_dir).mkdir(exist_ok=True)
    owl_test_file = Path(ROOT_DIR) / 'tests' / 'resources' / 'efo_sample.owl'
    yield yaml, owl_test_file
    # teardown
    shutil.rmtree(test_dir)


def test_run_riot(riot_inputs: tuple):
    """Should not throw exceptions or errors"""
    yaml, owl_test_file = riot_inputs
    riot = Riot(yaml.config)
    json_out = "efo_test.json"
    assert riot.run_riot(
        owl_file=owl_test_file,
        dir_output=yaml.config.output_dir,
        json_file=json_out,
        owl_jq=yaml.disease.etl.efo.owl_jq,
    )


def test_run_riot_JNI_error(riot_inputs: tuple):
    """JNI ERROR: lowering the JVM memory causes this."""
    yaml, owl_test_file = riot_inputs
    riot = Riot(yaml.config)
    # configure jvm with small memory
    yaml.config.java_vm = "-Xms2m -Xmx2m"
    json_out = "efo_test.json"
    with pytest.raises(RiotException):
        riot.run_riot(
            owl_file=owl_test_file,
            dir_output=yaml.config.output_dir,
            json_file=json_out,
            owl_jq=yaml.disease.etl.efo.owl_jq,
        )


def test_run_riot_no_owl_file(riot_inputs: tuple):
    """No OWL file"""
    yaml, _ = riot_inputs
    riot = Riot(yaml.config)
    owl_test_file = "DOES_NOT_EXIST.owl"
    json_out = "efo_test.json"
    with pytest.raises(RiotException):
        riot.run_riot(
            owl_file=owl_test_file,
            dir_output=yaml.config.output_dir,
            json_file=json_out,
            owl_jq=yaml.disease.etl.efo.owl_jq,
        )


def test_run_riot_empty_owl_file(riot_inputs: tuple):
    """Empty OWL file"""
    yaml, owl_test_file = riot_inputs
    riot = Riot(yaml.config)
    owl_test_file = Path(yaml.config.output_dir).joinpath("empty.owl")
    with open(owl_test_file, "w") as f:
        f.write("")
    json_out = "efo_test.json"
    with pytest.raises(RiotException):
        riot.run_riot(
            owl_file=owl_test_file,
            dir_output=yaml.config.output_dir,
            json_file=json_out,
            owl_jq=yaml.disease.etl.efo.owl_jq,
        )


def test_run_riot_malformed_owl_file(riot_inputs: tuple):
    """Malformed OWL file"""
    yaml, owl_test_file = riot_inputs
    riot = Riot(yaml.config)
    owl_test_file = Path(yaml.config.output_dir).joinpath("bad.owl")
    with open(owl_test_file, "w") as f:
        f.write("This is not OWL content")
    json_out = "efo_test.json"
    with pytest.raises(RiotException):
        riot.run_riot(
            owl_file=owl_test_file,
            dir_output=yaml.config.output_dir,
            json_file=json_out,
            owl_jq=yaml.disease.etl.efo.owl_jq,
        )


def test_convert_owl_to_jsonld_should_pass(riot_inputs: tuple):
    yaml, owl_test_file = riot_inputs
    riot = Riot(yaml.config)
    assert riot.convert_owl_to_jsonld(
        owl_file=owl_test_file,
        output_dir=yaml.config.output_dir,
        owl_jq=yaml.disease.etl.efo.owl_jq,
    )


def test_convert_owl_to_jsonld_should_fail(riot_inputs: tuple):
    """No OWL file"""
    yaml, _ = riot_inputs
    riot = Riot(yaml.config)
    owl_test_file = "DOES_NOT_EXIST.owl"
    with pytest.raises(RiotException):
        riot.convert_owl_to_jsonld(
            owl_file=owl_test_file,
            output_dir=yaml.config.output_dir,
            owl_jq=yaml.disease.etl.efo.owl_jq,
        )

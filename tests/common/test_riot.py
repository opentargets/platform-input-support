import pathlib
import pytest
import shutil

from modules.common.Riot import Riot, RiotException
from modules.common.YAMLReader import YAMLReader


@pytest.fixture()
def yaml():
    """Create the test config"""
    # setup
    test_output_dir = "tests/riot_output"
    yaml = YAMLReader(None).read_yaml()
    yaml.config.output_dir = test_output_dir
    pathlib.Path(test_output_dir).mkdir(exist_ok=True)
    yield yaml
    # teardown
    shutil.rmtree(test_output_dir)


@pytest.mark.skip(reason="Can only with riot, jq and a large efo owl file")
def test_run_riot_not_enough_memory(yaml):
    riot = Riot(yaml.config)
    # configure jvm with small memory
    yaml.config.java_vm = "-Xms2m -Xmx2m"
    owl_test_file = "tests/resources/efo_sample.owl"
    json_out = "efo_test.json"
    with pytest.raises(RiotException):
        riot.run_riot(
            owl_file=owl_test_file,
            dir_output=yaml.config.output_dir,
            json_file=json_out,
            owl_jq=yaml.disease.etl.efo.owl_jq,
        )


@pytest.mark.skip(reason="Can only with riot, jq and a large efo owl file")
def test_run_riot_with_enough_memory(yaml):
    riot = Riot(yaml.config)
    owl_test_file = "tests/resources/efo_sample.owl"
    # config jvm with enough memory
    yaml.config.java_vm = "-Xms4096m -Xmx8192m"
    json_out = "efo_test.json"
    riot.run_riot(
        owl_file=owl_test_file,
        dir_output=yaml.config.output_dir,
        json_file=json_out,
        owl_jq=yaml.disease.etl.efo.owl_jq,
    )

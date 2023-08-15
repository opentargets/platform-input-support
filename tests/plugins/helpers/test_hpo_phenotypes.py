import jsonlines
import pathlib
import pytest
import shutil
from collections import namedtuple

from plugins.helpers.HPOPhenotypes import HPOPhenotypes


@pytest.fixture()
def resources():
    """Create the test config and args"""
    # setup
    hpo_input_file = "tests/resources/phenotype.hpoa"
    test_dir = pathlib.Path("tests/hpo_pheno_out")
    test_dir.mkdir(exist_ok=True)
    hpo_output_file = test_dir.joinpath("hpo-phenotypes.jsonl")
    Resources = namedtuple("resources", "infile outfile")
    yield Resources(hpo_input_file, hpo_output_file)
    # teardown
    shutil.rmtree(test_dir)


def test_run(resources: namedtuple) -> None:
    """Test the run method doesn't read the header row"""
    hpo = HPOPhenotypes(hpo_input=resources.infile)
    hpo.run(str(resources.outfile))
    with jsonlines.open(resources.outfile) as reader:
        first_line = reader.read()
    assert first_line['databaseId'] != 'database_id'

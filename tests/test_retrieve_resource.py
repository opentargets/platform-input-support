import pytest

from platform_input_support.modules.common.YAMLReader import YAMLReader
from munch import Munch
from platform_input_support.modules.RetrieveResource import RetrieveResource


@pytest.fixture()
def resources():
    """Create the test config and args necessary to instantiate a manifest service"""
    # setup
    yaml = YAMLReader(None).read_yaml()
    args = Munch.fromDict({"steps": [], "exclude": []})
    yield yaml, args
    # teardown


def test_steps_logging_one_found(resources: tuple, caplog) -> None:
    yaml, args = resources
    args.steps = ["disease"]
    r = RetrieveResource(args, yaml)
    r.init_plugins()
    steps_to_run = r.steps()
    assert len(steps_to_run) == 1
    log_count = 0
    for record in caplog.records:
        if "Steps NOT FOUND" in record.msg:
            log_count += 1
    assert log_count == 0


def test_steps_logging_not_found(resources: tuple, caplog) -> None:
    yaml, args = resources
    args.steps = ["not_a_step"]
    r = RetrieveResource(args, yaml)
    r.init_plugins()
    steps_to_run = r.steps()
    assert len(steps_to_run) == 0
    log_count = 0
    for record in caplog.records:
        if "Steps NOT FOUND" in record.msg:
            log_count += 1
    assert log_count == 1
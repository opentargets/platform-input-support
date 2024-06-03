import pytest
from munch import Munch

from platform_input_support.modules.common.yaml_reader import YAMLReader
from platform_input_support.modules.retrieve_resource import RetrieveResource


@pytest.fixture
def resources():
    """Create the test config and args necessary to instantiate a manifest service."""
    yaml = YAMLReader(None).read_yaml()
    args = Munch.fromDict({'steps': [], 'exclude': []})
    return yaml, args


def test_steps_logging_one_found(resources: tuple, caplog) -> None:
    yaml, args = resources
    args.steps = ['disease']
    r = RetrieveResource(args, yaml)
    r.init_plugins()
    steps_to_run = r.steps()
    assert len(steps_to_run) == 1
    log_count = 0
    for record in caplog.records:
        if 'Steps NOT FOUND' in record.msg:
            log_count += 1
    assert log_count == 0


def test_steps_logging_not_found(resources: tuple, caplog) -> None:
    yaml, args = resources
    args.steps = ['not_a_step']
    r = RetrieveResource(args, yaml)
    r.init_plugins()
    steps_to_run = r.steps()
    assert len(steps_to_run) == 0
    log_count = 0
    for record in caplog.records:
        if 'Steps NOT FOUND' in record.msg:
            log_count += 1
    assert log_count == 1

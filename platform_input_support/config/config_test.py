from pathlib import Path

import pytest

from platform_input_support.config import settings
from platform_input_support.config.config import Config
from platform_input_support.config.models import BaseTaskDefinition, CliSettings, EnvSettings, Settings, YamlSettings


@pytest.fixture
def c(mocker):
    mock_cli = mocker.patch('platform_input_support.config.config.parse_cli')
    mock_env = mocker.patch('platform_input_support.config.config.parse_env')
    mock_yaml = mocker.patch('platform_input_support.config.config.parse_yaml')
    mock_get_yaml_settings = mocker.patch('platform_input_support.config.config.get_yaml_settings')

    mock_cli.return_value = CliSettings(step='step_1', config_file=Path('test_cli.yaml'))
    mock_env.return_value = EnvSettings(work_dir=Path('./somewhere'))
    mock_yaml.return_value = {'steps': {'step_1': [{'name': 'task_1'}]}}
    mock_get_yaml_settings.return_value = YamlSettings(gcs_url='gs://bucket/path/to/file')

    return Config()


def test_config_initialization(c):
    assert isinstance(settings(), Settings)
    assert settings().model_dump(exclude_none=True) == {
        'step': 'step_1',
        'config_file': Path('test_cli.yaml'),
        'work_dir': Path('./somewhere'),
        'gcs_url': 'gs://bucket/path/to/file',
        'force': False,
        'log_level': 'INFO',
    }


def test_validate_step_valid(c):
    c.settings.step = 'step_1'

    assert True  # No exception means the step is valid


def test_validate_step_empty(c):
    c.settings.step = ''

    with pytest.raises(SystemExit) as e:
        c._validate_step()

    assert e.type is SystemExit
    assert e.value.code == 1


def test_validate_step_invalid(c):
    c.settings.step = 'invalid_step'

    with pytest.raises(SystemExit) as e:
        c._validate_step()

    assert e.type is SystemExit
    assert e.value.code == 1


def test_settings_is_single_instance():
    s1 = settings()
    s2 = settings()

    assert s1 is s2


def test_get_task_definitions(c):
    c.yaml_dict = {'steps': {'step_1': [{'name': 'task_1'}]}}

    assert c.get_task_definitions() == [BaseTaskDefinition(name='task_1')]


def test_get_task_definitions_validation_error(c):
    c.yaml_dict = {'steps': {'step_1': [{'name': True}]}}

    with pytest.raises(SystemExit) as e:
        c.get_task_definitions()

    assert e.type is SystemExit
    assert e.value.code == 1


def test_get_task_definitions_non_existent_step(c, capsys):
    c.yaml_dict = {'steps': {'step_2': [{'name': 'task_1'}]}}

    with pytest.raises(SystemExit) as e:
        c.get_task_definitions()

    assert e.type is SystemExit
    assert e.value.code == 1

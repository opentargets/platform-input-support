import os
from pathlib import Path

import pytest

from platform_input_support.config.models import BaseTaskDefinition, YamlSettings
from platform_input_support.config.yaml import (
    get_yaml_sentinel_dict,
    get_yaml_settings,
    get_yaml_stepdefs,
    load_yaml_file,
    parse_yaml,
    parse_yaml_string,
)

# mock dicts for testing validate_config_parts
CONFIG_DICT_VALID = {
    'work_dir': './somewhere',
    'gcs_url': 'gs://bucket/path/to/file',
    'log_level': 'INFO',
    'force': False,
    'steps': {
        'step_1': [
            {
                'name': 'download file 1',
                'source': 'http://example.com/file1.txt',
                'destination': 'somewhere/file1.txt',
            }
        ],
        'step_2': [
            {
                'name': 'download file 2',
                'source': 'http://example.com/file2.txt',
                'destination': 'somewhere/file2.txt',
            }
        ],
    },
    'scratchpad': {
        'some.label.to.replace': 'thisvalue',
    },
}

CONFIG_DICT_INVALID = {'force': 'not_a_bool'}

CONFIG_DICT_STEPS_ARE_LIST = {
    'work_dir': './somewhere',
    'gcs_url': 'gs://bucket/path/to/file',
    'log_level': 'INFO',
    'force': False,
    'steps': [
        {
            'name': 'download file 1',
        }
    ],
}

CONFIG_DICT_STEPS_ARE_INVALID = {
    'work_dir': './somewhere',
    'gcs_url': 'gs://bucket/path/to/file',
    'log_level': 'INFO',
    'force': False,
    'steps': {
        'step_1': [
            {
                'name': False,
            }
        ]
    },
}

CONFIG_DICT_MISSING_STEPS = {
    'work_dir': './somewhere',
    'gcs_url': 'gs://bucket/path/to/file',
    'log_level': 'INFO',
    'force': False,
    'scratchpad': {
        'some.label.to.replace': 'thisvalue',
    },
}

# mock yamls for testing parse_yaml
YAML_CONTENT_VALID = """
work_dir: ./somewhere
gcs_url: gs://bucket/path/to/file
log_level: INFO
force: no
steps:
  step_1:
    - name: download file 1
      source: http://example.com/file1.txt
      destination: somewhere/file1.txt
  step_2:
    - name: download file 2
      source: http://example.com/file2.txt
      destination: somewhere/file2.txt
scratchpad:
  some.label.to.replace: thisvalue
"""

YAML_CONTENT_INVALID = """
steps
  step_1:
  - name: download file 1
    destination: somewhere/file1.txt
"""

YAML_CONTENT_MISSING_STEPS = """
work_dir: ./somewhere
gcs_url: gs://bucket/path/to/file
log_level: INFO
force: no
scratchpad:
  some.label.to.replace: thisvalue
"""

YAML_CONTENT_MISSING_SCRATCHPAD = """
work_dir: ./somewhere
gcs_url: gs://bucket/path/to/file
log_level: INFO
force: no
steps:
    step_1:
      - name: download file 1
        source: http://example.com/file1.txt
        destination: somewhere/file1.txt
    step_2:
      - name: download file 2
        source: http://example.com/file2.txt
        destination: somewhere/file2.txt
"""


@pytest.fixture
def temp_yaml_file_factory(tmp_path):
    """Fixture to create a temporary YAML file with data from a provided dictionary."""

    def _create_temp_yaml_file(yaml_content: str | None = None):
        if not yaml_content:
            yaml_content = 'key: value'
        d = tmp_path / 'sub'
        d.mkdir()
        p = d / 'test.yaml'
        p.write_text(yaml_content)
        return p

    return _create_temp_yaml_file


def test_load_yaml_file_valid_data(temp_yaml_file_factory):
    temp_yaml_file = temp_yaml_file_factory()

    content = load_yaml_file(temp_yaml_file)

    assert content == 'key: value'


# Test load_yaml_file with invalid data
def test_load_yaml_file_non_existent_file(tmp_path):
    non_existent_file = tmp_path / 'does_not_exist.yaml'

    with pytest.raises(SystemExit) as e:
        load_yaml_file(non_existent_file)

    assert e.type is SystemExit
    assert e.value.code == 1


@pytest.mark.skipif(os.name != 'posix', reason='Permission test is Unix specific')
def test_load_yaml_file_no_permissions(tmp_path):
    p = tmp_path / 'test.yaml'
    p.write_text('key: value')
    p.chmod(0o000)  # no permissions

    with pytest.raises(SystemExit) as e:
        load_yaml_file(p)

    assert e.type is SystemExit
    assert e.value.code == 1

    p.chmod(0o644)  # reset permissions to avoid issues with cleanup


@pytest.mark.skipif(os.name != 'posix', reason='OSError simulation is Unix specific')
def test_load_yaml_file_generic_os_error(tmp_path, monkeypatch):
    def mock_read_text(*args, **kwargs):
        raise OSError('Generic OS error')

    monkeypatch.setattr(Path, 'read_text', mock_read_text)
    p = tmp_path / 'test.yaml'

    with pytest.raises(SystemExit) as e:
        load_yaml_file(p)

    assert e.type is SystemExit
    assert e.value.code == 1


def test_parse_yaml_str_valid_data():
    yaml_string = 'key: value'

    result = parse_yaml_string(yaml_string)

    assert result == {'key': 'value'}


def test_parse_yaml_string_invalid_yaml():
    yaml_string = 'key: value\ninvalid_yaml'

    with pytest.raises(SystemExit) as e:
        parse_yaml_string(yaml_string)

    assert e.type is SystemExit
    assert e.value.code == 1


def test_parse_yaml_string_empty_string():
    yaml_string = ''

    result = parse_yaml_string(yaml_string)

    assert result == {}


def test_parse_yaml_valid_data(temp_yaml_file_factory):
    temp_yaml_file = temp_yaml_file_factory(YAML_CONTENT_VALID)

    yaml_dict = parse_yaml(temp_yaml_file)

    assert yaml_dict == CONFIG_DICT_VALID


def test_get_yaml_settings_valid():
    settings = get_yaml_settings(CONFIG_DICT_VALID)

    assert isinstance(settings, YamlSettings)
    assert settings.work_dir == Path('./somewhere')
    assert settings.gcs_url == 'gs://bucket/path/to/file'
    assert settings.force is False
    assert settings.log_level == 'INFO'


def test_get_yaml_settings_missing_fields():
    with pytest.raises(SystemExit) as e:
        get_yaml_settings(CONFIG_DICT_INVALID)

    assert e.type is SystemExit
    assert e.value.code == 1


def test_get_yaml_stepdefs_valid_data():
    stepdefs = get_yaml_stepdefs(CONFIG_DICT_VALID)

    assert isinstance(stepdefs, dict)
    assert 'step_1' in stepdefs
    assert isinstance(stepdefs['step_1'], list)
    assert len(stepdefs['step_1']) == 1
    assert isinstance(stepdefs['step_1'][0], BaseTaskDefinition)
    assert stepdefs['step_1'][0].model_dump() == {
        'name': 'download file 1',
        'source': 'http://example.com/file1.txt',
        'destination': 'somewhere/file1.txt',
    }
    assert 'step_2' in stepdefs
    assert isinstance(stepdefs['step_2'], list)
    assert len(stepdefs['step_2']) == 1
    assert isinstance(stepdefs['step_2'][0], BaseTaskDefinition)
    assert stepdefs['step_2'][0].model_dump() == {
        'name': 'download file 2',
        'source': 'http://example.com/file2.txt',
        'destination': 'somewhere/file2.txt',
    }


def test_get_yaml_stepdefs_missing_steps():
    stepdefs = get_yaml_stepdefs(CONFIG_DICT_MISSING_STEPS)
    assert stepdefs == {}


def test_get_yaml_stepdefs_invalid_yaml():
    with pytest.raises(SystemExit) as e:
        get_yaml_stepdefs(CONFIG_DICT_STEPS_ARE_INVALID)

    assert e.type is SystemExit
    assert e.value.code == 1


def test_get_yaml_stepdefs_steps_are_list():
    with pytest.raises(SystemExit) as e:
        get_yaml_stepdefs(CONFIG_DICT_STEPS_ARE_LIST)

    assert e.type is SystemExit
    assert e.value.code == 1


def test_get_yaml_sentinel_dict_valid():
    sentinel_dict = get_yaml_sentinel_dict(CONFIG_DICT_VALID)

    assert isinstance(sentinel_dict, dict)
    assert sentinel_dict == {'some.label.to.replace': 'thisvalue'}


def test_get_yaml_sentinel_dict_missing_scratchpad():
    sentinel_dict = get_yaml_sentinel_dict(parse_yaml_string(YAML_CONTENT_MISSING_SCRATCHPAD))

    assert isinstance(sentinel_dict, dict)
    assert sentinel_dict == {}

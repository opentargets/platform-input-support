import os
from pathlib import Path

import pytest

from platform_input_support.config.env import ENV_PREFIX, parse_env
from platform_input_support.config.models import EnvSettings


def test_parse_env_with_variables(monkeypatch):
    monkeypatch.setenv(f'{ENV_PREFIX}_STEP', 'go')
    monkeypatch.setenv(f'{ENV_PREFIX}_CONFIG_FILE', '/path/to/file')
    monkeypatch.setenv(f'{ENV_PREFIX}_FORCE', 'y')

    settings = parse_env()

    assert isinstance(settings, EnvSettings)
    assert settings.step == 'go'
    assert settings.config_file == Path('/path/to/file')
    assert settings.force


def test_parse_env_without_relevant_variables(monkeypatch):
    for var in list(filter(lambda v: v.startswith(f'{ENV_PREFIX}_'), os.environ.keys())):
        monkeypatch.delenv(var)

    settings = parse_env()

    assert isinstance(settings, EnvSettings)
    assert settings.model_dump(exclude_none=True) == {}


def test_parse_env_with_invalid_variables(monkeypatch):
    monkeypatch.setenv(f'{ENV_PREFIX}_FORCE', 'this_is_not_a_boolean')

    with pytest.raises(SystemExit):
        parse_env()

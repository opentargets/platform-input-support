import os
from pathlib import Path

import pytest

from pis.config.env import ENV_PREFIX, parse_env
from pis.config.models import EnvSettings


def test_parse_env_with_variables(monkeypatch):
    monkeypatch.setenv(f'{ENV_PREFIX}_STEP', 'go')
    monkeypatch.setenv(f'{ENV_PREFIX}_CONFIG_FILE', '/path/to/file')
    monkeypatch.setenv(f'{ENV_PREFIX}_POOL', '5')

    settings = parse_env()

    assert isinstance(settings, EnvSettings)
    assert settings.step == 'go'
    assert settings.config_file == Path('/path/to/file')
    assert settings.pool == 5


def test_parse_env_without_relevant_variables(monkeypatch):
    for var in list(filter(lambda v: v.startswith(f'{ENV_PREFIX}_'), os.environ.keys())):
        monkeypatch.delenv(var)

    settings = parse_env()

    assert isinstance(settings, EnvSettings)
    assert settings.model_dump(exclude_none=True) == {}


def test_parse_env_with_invalid_variables(monkeypatch):
    monkeypatch.setenv(f'{ENV_PREFIX}_POOL', 'this_is_not_an_integer')

    with pytest.raises(SystemExit):
        parse_env()

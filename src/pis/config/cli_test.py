import re
from pathlib import Path

import pytest

from pis.config.cli import parse_cli


def test_parse_cli_without_arguments(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        [
            'cli.py',
        ],
    )

    with pytest.raises(SystemExit):
        parse_cli()


def test_parse_cli_with_step_argument(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        [
            'cli.py',
            '--step',
            'validation',
        ],
    )

    settings = parse_cli()

    assert settings.step == 'validation'


def test_parse_cli_with_config_file_argument(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        [
            'cli.py',
            '--step',
            'validation',
            '--config-file',
            'config.json',
        ],
    )

    settings = parse_cli()

    assert settings.config_file == Path('config.json')


def test_parse_cli_with_work_dir_argument(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        [
            'cli.py',
            '--step',
            'validation',
            '--work-dir',
            '/somewhere',
        ],
    )

    settings = parse_cli()

    assert settings.work_dir == Path('/somewhere')


def test_parse_cli_with_remote_uri_argument(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        [
            'cli.py',
            '--step',
            'validation',
            '--remote-uri',
            'gs://bucket/path',
        ],
    )

    settings = parse_cli()

    assert settings.remote_uri == 'gs://bucket/path'


def test_parse_cli_with_pool_argument(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        [
            'cli.py',
            '--pool',
            '10',
            '--step',
            'validation',
        ],
    )

    settings = parse_cli()

    assert settings.pool == 10


def test_parse_cli_help_contains_env_var_and_default(monkeypatch, capsys):
    def clean_output(output):
        return re.sub(r'\n\s*', ' ', output)

    monkeypatch.setattr('sys.argv', ['cli.py', '-h'])

    with pytest.raises(SystemExit):
        parse_cli()
    captured = capsys.readouterr()
    out = clean_output(captured.out)

    assert '(environment variable: PIS_POOL)' in out
    assert '(default: 5)' in out

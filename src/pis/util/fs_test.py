from pathlib import Path
from unittest.mock import patch

import pytest

from pis.util.fs import check_dir, check_file


@pytest.fixture
def mock_path_funcs(monkeypatch):
    def mock(*args, **kwargs):
        raise OSError('Mocked error')

    monkeypatch.setattr(Path, 'mkdir', mock)
    monkeypatch.setattr(Path, 'unlink', mock)


@patch('pis.util.fs.absolute_path')
def test_check_dir_with_existing_dir(mock_absolute_path, tmp_path):
    path = tmp_path / 'existing_dir'
    mock_absolute_path.return_value = path
    path.mkdir()

    check_dir(path)

    assert path.is_dir()


@patch('pis.util.fs.absolute_path')
def test_check_dir_with_non_existing_dir(mock_absolute_path, tmp_path):
    path = tmp_path / 'nothing' / 'afile.txt'
    mock_absolute_path.return_value = path

    assert not path.exists()

    check_dir(path)

    assert path.parent.is_dir()
    assert not path.is_file()


def test_check_dir_with_non_existing_dir_oserror(tmp_path, mock_path_funcs):
    path = tmp_path / 'nothing' / 'afile.txt'

    assert not path.exists()

    with pytest.raises(SystemExit):
        check_dir(path)

    assert not path.parent.is_dir()
    assert not path.is_file()


@patch('pis.util.fs.absolute_path')
def test_check_dir_with_no_permission(mock_absolute_path, tmp_path):
    path = tmp_path / 'no_permission'
    mock_absolute_path.return_value = path
    path.mkdir()
    path.chmod(0o000)

    with pytest.raises(SystemExit):
        check_dir(path)

    path.chmod(0o755)
    path.rmdir()


@patch('pis.util.fs.absolute_path')
def test_check_file_with_existing_file_is_deleted(mock_absolute_path, tmp_path):
    path = tmp_path / 'existing_file'
    mock_absolute_path.return_value = path
    path.touch()

    assert path.is_file()

    check_file(path)

    assert not path.is_file()


def test_check_dir_with_file_oserror(tmp_path, mock_path_funcs):
    path = tmp_path / 'existing_file'
    path.touch()

    assert path.is_file()

    with pytest.raises(SystemExit):
        check_dir(path)

    assert path.is_file()

from pathlib import Path

import pytest

from platform_input_support.util.fs import check_dir


@pytest.fixture
def mock_path_funcs(monkeypatch):
    def mock(*args, **kwargs):
        raise OSError('Mocked error')

    monkeypatch.setattr(Path, 'mkdir', mock)
    monkeypatch.setattr(Path, 'unlink', mock)


def test_check_dir_with_existing_dir(tmp_path):
    path = tmp_path / 'existing_dir'
    path.mkdir()

    check_dir(path)

    assert path.is_dir()


def test_check_dir_with_non_existing_dir(tmp_path):
    path = tmp_path / 'nothing' / 'afile.txt'

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


def test_check_dir_with_no_permission(tmp_path):
    path = tmp_path / 'no_permission' / 'afile.txt'
    path.parent.mkdir()
    path.parent.chmod(0o000)

    with pytest.raises(SystemExit):
        check_dir(path)

    path.parent.chmod(0o755)
    path.parent.rmdir()


def test_check_dir_with_existing_file(tmp_path):
    path = tmp_path / 'existing_file'
    path.touch()

    assert path.is_file()

    check_dir(path)

    assert not path.is_file()


def test_check_dir_with_existing_file_oserror(tmp_path, mock_path_funcs):
    path = tmp_path / 'existing_file'
    path.touch()

    assert path.is_file()

    with pytest.raises(SystemExit):
        check_dir(path)

    assert path.is_file()

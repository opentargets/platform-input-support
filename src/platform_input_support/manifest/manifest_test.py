import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from filelock import Timeout
from freezegun import freeze_time

from platform_input_support.config.models import Settings
from platform_input_support.manifest import Manifest
from platform_input_support.manifest.models import Result, RootManifest, StepManifest
from platform_input_support.util.errors import HelperError, NotFoundError, PISCriticalError, PreconditionFailedError

s = Settings(step='step1', remote_uri='gs://test')
steps = ['step1', 'step2']
content_dict = {
    'result': 'failed',
    'created': '2024-06-26T08:23:40.126926Z',
    'modified': '2024-06-27T10:41:06.852548',
    'log': ['---- [ 2024-06-27 10:41:06 run summary ]----', '1 completed steps', '1 failed steps'],
    'steps': {
        'step1': {
            'name': 'step1',
            'result': 'completed',
        },
        'step2': {
            'name': 'step2',
            'result': 'failed',
        },
    },
}
content_json = json.dumps(content_dict)

with freeze_time('2024-06-27 10:00:00'):
    manifest_steps = {
        'step1': StepManifest(name='step1', result=Result.COMPLETED, log=[], tasks=[]),
        'step2': StepManifest(name='step2', result=Result.FAILED, log=[], tasks=[]),
    }

    new_manifest_steps = {
        'step1': StepManifest(name='step1', result=Result.PENDING, log=[], tasks=[]),
        'step2': StepManifest(name='step2', result=Result.PENDING, log=[], tasks=[]),
    }


@pytest.fixture(autouse=True)
def mocked_settings():
    with patch('platform_input_support.manifest.manifest.settings') as mock_settings:
        mock_settings.return_value = s
        yield mock_settings


@pytest.fixture(autouse=True)
def mocked_steps():
    with patch('platform_input_support.manifest.manifest.steps') as mock_steps:
        mock_steps.return_value = steps
        yield mock_steps


@pytest.fixture(autouse=True)
def mocked_absolute_path():
    with patch('platform_input_support.manifest.manifest.absolute_path') as mock_absolute_path:
        mock_absolute_path.return_value = MagicMock(Path('path/to/manifest.json'))
        mock_absolute_path.return_value.read_text.return_value = content_json
        yield mock_absolute_path


@patch('platform_input_support.manifest.manifest.get_remote_storage')
def test_load_remote_ok(mock_remote_storage):
    mock_remote_storage.return_value.download_to_string.return_value = (content_json, 81235723895)

    m = Manifest()

    assert isinstance(m._manifest, RootManifest)
    assert len(m._manifest.steps) == 2
    assert m._revision == 81235723895
    assert m._manifest.steps == manifest_steps
    mock_remote_storage.return_value.download_to_string.assert_called_once()


@patch('platform_input_support.manifest.manifest.get_remote_storage')
def test_load_remote_ko(mock_remote_storage):
    mock_remote_storage.return_value.download_to_string.side_effect = NotFoundError()

    m = Manifest()

    assert isinstance(m._manifest, RootManifest)
    assert len(m._manifest.steps) == 2
    assert m._revision == 0
    assert m._manifest.steps == manifest_steps
    mock_remote_storage.return_value.download_to_string.assert_called_once()


@patch('platform_input_support.manifest.manifest.Manifest._load_remote')
def test_load_local_ok(
    mock_load_remote,
    mocked_absolute_path,
):
    mock_load_remote.return_value = None

    m = Manifest()

    assert isinstance(m._manifest, RootManifest)
    assert len(m._manifest.steps) == 2
    assert m._revision == 0
    assert m._manifest.steps == manifest_steps
    mock_load_remote.assert_called_once()
    mocked_absolute_path.return_value.read_text.assert_called_once()


@patch('platform_input_support.manifest.manifest.Manifest._load_remote')
def test_load_local_ko(
    mock_load_remote,
    mocked_absolute_path,
):
    mock_load_remote.return_value = None
    mocked_absolute_path.return_value.read_text.side_effect = FileNotFoundError()

    m = Manifest()

    assert isinstance(m._manifest, RootManifest)
    assert len(m._manifest.steps) == 2
    assert m._revision == 0
    assert m._manifest.steps == new_manifest_steps
    mock_load_remote.assert_called_once()
    mocked_absolute_path.return_value.read_text.assert_called_once()


@patch('platform_input_support.manifest.manifest.Manifest._load_remote')
@patch('platform_input_support.manifest.manifest.Manifest._load_local')
def test_create_empty_ok(mock_load_remote, mock_load_local):
    m = Manifest()

    mock_load_remote.return_value = None
    mock_load_local.return_value = None

    r = m._create_empty()

    assert r.steps == new_manifest_steps


@patch('platform_input_support.manifest.manifest.get_remote_storage')
def test_save_remote_ok(mock_remote_storage):
    mock_remote_storage.return_value.download_to_string.return_value = (content_json, 81235723895)
    m = Manifest()

    m._save_remote()

    assert mock_remote_storage.return_value.upload.call_count == 1


@patch('time.sleep')
@patch('platform_input_support.manifest.manifest.Manifest._refresh_from_remote')
@patch('platform_input_support.manifest.manifest.get_remote_storage')
def test_save_remote_ok_retries(
    mock_remote_storage,
    mock_refresh_from_remote,
    mock_time_sleep,
):
    mock_remote_storage.return_value.download_to_string.return_value = (content_json, 81235723895)
    mock_remote_storage.return_value.upload.side_effect = [PreconditionFailedError, PreconditionFailedError, None]
    m = Manifest()
    m._revision = 123

    m._save_remote()

    assert mock_remote_storage.return_value.upload.call_count == 3
    assert mock_time_sleep.call_count == 2


@patch('platform_input_support.manifest.manifest.Manifest._refresh_from_remote')
@patch('platform_input_support.manifest.manifest.get_remote_storage')
def test_save_remote_ko(mock_remote_storage, mock_refresh_from_remote):
    mock_remote_storage.return_value.download_to_string.return_value = (content_json, 81235723895)
    mock_remote_storage.return_value.upload.side_effect = HelperError('test')
    m = Manifest()
    m._revision = 1

    with pytest.raises(PISCriticalError):
        m._save_remote()


@patch('platform_input_support.manifest.manifest.Manifest._load_remote')
@patch('platform_input_support.manifest.manifest.FileLock')
@patch('platform_input_support.manifest.manifest.absolute_path')
@freeze_time('2024-06-27 10:00:00')
def test_save_local_ok(mock_absolute_path, mock_file_lock, mock_load_remote, tmp_path):
    the_manifest = RootManifest.model_validate_json(content_json)
    manifest_path = tmp_path / 'manifest.json'
    mock_absolute_path.return_value = manifest_path
    mock_load_remote.return_value = the_manifest
    mock_file_lock.return_value.acquire = lambda: True
    m = Manifest()

    m._save_local()

    read_manifest = RootManifest.model_validate_json(manifest_path.read_text())
    assert manifest_path.is_file()
    assert read_manifest == the_manifest


@patch('platform_input_support.manifest.manifest.Manifest._load_remote')
@patch('platform_input_support.manifest.manifest.FileLock')
@patch('platform_input_support.manifest.manifest.absolute_path')
def test_save_local_ko(mock_absolute_path, mock_file_lock, mock_load_remote):
    the_manifest = RootManifest.model_validate_json(content_json)
    mock_absolute_path.return_value.write_text.side_effect = OSError()
    mock_file_lock.return_value.acquire = lambda: True
    mock_load_remote.return_value = the_manifest
    m = Manifest()

    with pytest.raises(PISCriticalError):
        m._save_local()


@patch('platform_input_support.manifest.manifest.Manifest._load_remote')
@patch('platform_input_support.manifest.manifest.Manifest._serialize')
@patch('platform_input_support.manifest.manifest.FileLock')
@patch('platform_input_support.manifest.manifest.absolute_path')
def test_save_local_ko_timeout(mock_absolute_path, mock_file_lock, mock_serialize, mock_load_remote, tmp_path):
    manifest_path = tmp_path / 'manifest.json'
    lockfile_path = tmp_path / 'manifest.json.lock'
    mock_absolute_path.return_value = manifest_path
    mock_file_lock.return_value.acquire.side_effect = [Timeout(lockfile_path)]
    mock_serialize.return_value = content_json
    mock_load_remote.return_value = None
    m = Manifest()

    with pytest.raises(PISCriticalError):
        m._save_local()

    assert not manifest_path.is_file()

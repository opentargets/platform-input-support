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

s = Settings(step='step1', gcs_url='gs://test')
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


@patch('platform_input_support.manifest.manifest.Manifest._load_gcs')
def test_load_manifest_with_manifest_found_in_gcs(mock_load_gcs):
    mock_load_gcs.return_value = (content_json, 81235723895)

    m = Manifest()

    assert isinstance(m._manifest, RootManifest)
    assert len(m._manifest.steps) == 2
    assert m._generation == 81235723895
    assert m._manifest.steps == manifest_steps
    mock_load_gcs.assert_called_once()


@patch('platform_input_support.manifest.manifest.Manifest._load_gcs')
@patch('platform_input_support.manifest.manifest.Manifest._load_local')
def test_load_manifest_with_manifest_found_locally(
    mock_load_local,
    mock_load_gcs,
):
    mock_load_gcs.return_value = None
    mock_load_local.return_value = (content_json, 1)

    m = Manifest()

    assert isinstance(m._manifest, RootManifest)
    assert len(m._manifest.steps) == 2
    assert m._generation == 1
    assert m._manifest.steps == manifest_steps
    mock_load_gcs.assert_called_once()
    mock_load_local.assert_called_once()


@patch('platform_input_support.manifest.manifest.Manifest._load_gcs')
@patch('platform_input_support.manifest.manifest.Manifest._load_local')
@patch('platform_input_support.manifest.manifest.Manifest._create_empty')
@patch('platform_input_support.manifest.manifest.steps')
@freeze_time('2024-06-27 10:00:00')
def test_init_manifest_with_no_prior_manifest(
    mock_steps,
    mock_create_empty,
    mock_load_local,
    mock_load_gcs,
):
    mock_steps.return_value = s
    mock_load_gcs.return_value = (None, 0)
    mock_load_local.return_value = (None, 0)
    mock_create_empty.return_value = RootManifest.model_validate_json(content_json)

    m = Manifest()

    assert isinstance(m._manifest, RootManifest)
    assert len(m._manifest.steps) == 2
    assert m._generation == 0
    assert m._manifest.steps == manifest_steps
    mock_create_empty.assert_called_once()


@patch('platform_input_support.manifest.manifest.google_helper')
@freeze_time('2024-06-27 10:00:00')
def test_load_gcs_manifest_found(mock_google_helper):
    mock_google_helper.return_value.is_ready = True
    mock_google_helper.return_value.download_to_string.return_value = (content_json, 283523)
    m = Manifest()

    manifest_str, generation = m._load_gcs() or (None, 0)

    assert manifest_str == content_json
    assert generation == 283523
    mock_google_helper.return_value.download_to_string.assert_called()


@patch('platform_input_support.manifest.manifest.google_helper')
@patch.object(Manifest, '__init__', return_value=None)
@freeze_time('2024-06-27 10:00:00')
def test_load_gcs_manifest_not_found(mock_init, mock_google_helper):
    mock_google_helper.return_value.is_ready = True
    mock_google_helper.return_value.download_to_string.side_effect = NotFoundError('t')
    m = Manifest()

    r = m._load_gcs()

    assert r is None
    mock_google_helper.return_value.download_to_string.assert_called()


@patch('platform_input_support.manifest.manifest.google_helper')
@patch.object(Manifest, '__init__', return_value=None)
@freeze_time('2024-06-27 10:00:00')
def test_load_gcs_manifest_google_helper_not_ready(mock_init, mock_google_helper):
    mock_google_helper.return_value.is_ready = False
    manifest = Manifest()

    with pytest.raises(PISCriticalError):
        manifest._load_gcs()


@patch('platform_input_support.manifest.manifest.Manifest._load_gcs')
@patch('platform_input_support.manifest.manifest.get_full_path')
def test_load_local_manifest_found(mock_get_full_path, mock_load_gcs):
    mock_load_gcs.return_value = None
    mock_get_full_path.return_value = MagicMock(spec=Path, value='path/to/manifest.json')
    mock_get_full_path.return_value.read_text.return_value = content_json
    m = Manifest()

    r = m._load_local()

    assert r == (content_json, 0)


@patch('platform_input_support.manifest.manifest.Manifest._load_gcs')
@patch('platform_input_support.manifest.manifest.get_full_path')
@patch('platform_input_support.manifest.manifest.Manifest._create_empty')
def test_load_local_manifest_not_found(mock_create_empty, mock_get_full_path, mock_load_gcs):
    mock_load_gcs.return_value = None
    mock_get_full_path.return_value = MagicMock(spec=Path, value='path/to/manifest.json')
    mock_get_full_path.return_value.read_text.side_effect = FileNotFoundError()
    mock_create_empty.return_value = RootManifest()
    m = Manifest()

    r = m._load_local()

    assert r is None
    mock_get_full_path.return_value.read_text.assert_called()


@patch('platform_input_support.manifest.manifest.Manifest._load_gcs')
@patch('platform_input_support.manifest.manifest.get_full_path')
@patch('platform_input_support.manifest.manifest.Manifest._create_empty')
def test_load_local_manifest_oserror(mock_create_empty, mock_get_full_path, mock_load_gcs):
    mock_load_gcs.return_value = None
    mock_get_full_path.return_value = MagicMock(spec=Path, value='path/to/manifest.json')
    # First time it's fine, for instantiation of m, then it raises OSError
    mock_get_full_path.return_value.read_text.side_effect = [None, OSError()]
    mock_create_empty.return_value = RootManifest()
    m = Manifest()

    with pytest.raises(PISCriticalError):
        m._load_local()


@patch('platform_input_support.manifest.manifest.steps')
@patch.object(Manifest, '__init__', return_value=None)
@freeze_time('2024-06-27 10:00:00')
def test_create_empty(mock_init, mock_steps):
    mock_steps.return_value = steps
    m = Manifest()

    r = m._create_empty()

    assert r.steps == new_manifest_steps


@patch('platform_input_support.manifest.manifest.Manifest._init_manifest')
@patch('platform_input_support.manifest.manifest.Manifest._serialize')
@patch('platform_input_support.manifest.manifest.FileLock')
@patch('platform_input_support.manifest.manifest.get_full_path')
def test_save_local_ok(mock_get_full_path, mock_file_lock, mock_serialize, mock_init_manifest, tmp_path):
    manifest_path = tmp_path / 'manifest.json'
    mock_get_full_path.return_value = manifest_path
    mock_serialize.return_value = content_json
    mock_file_lock.return_value.acquire = lambda: True
    m = Manifest()

    m._save_local()

    assert manifest_path.is_file()
    assert manifest_path.read_text() == content_json


@patch('platform_input_support.manifest.manifest.Manifest._init_manifest')
@patch('platform_input_support.manifest.manifest.Manifest._serialize')
@patch('platform_input_support.manifest.manifest.FileLock')
@patch('platform_input_support.manifest.manifest.get_full_path')
def test_save_local_ko(mock_get_full_path, mock_file_lock, mock_serialize, mock_init_manifest, tmp_path):
    mock_get_full_path.return_value = MagicMock(spec=Path, value=tmp_path / 'manifest.json')
    mock_get_full_path.return_value.write_text.side_effect = OSError
    mock_serialize.return_value = content_json
    mock_file_lock.return_value.acquire = lambda: True
    m = Manifest()

    with pytest.raises(PISCriticalError):
        m._save_local()


@patch('platform_input_support.manifest.manifest.Manifest._init_manifest')
@patch('platform_input_support.manifest.manifest.Manifest._serialize')
@patch('platform_input_support.manifest.manifest.FileLock')
@patch('platform_input_support.manifest.manifest.get_full_path')
def test_save_local_timeout(mock_get_full_path, mock_file_lock, mock_serialize, mock_init_manifest, tmp_path):
    manifest_path = tmp_path / 'manifest.json'
    lockfile_path = tmp_path / 'manifest.json.lock'
    mock_get_full_path.return_value = manifest_path
    mock_serialize.return_value = content_json
    mock_file_lock.return_value.acquire.side_effect = [Timeout(lockfile_path)]
    m = Manifest()

    with pytest.raises(PISCriticalError):
        m._save_local()

    assert not manifest_path.is_file()


@patch('platform_input_support.manifest.manifest.Manifest._init_manifest')
@patch('platform_input_support.manifest.manifest.Manifest._serialize')
@patch('platform_input_support.manifest.manifest.google_helper')
def test_save_gcs_ok(mock_google_helper, mock_serialize, mock_init_manifest):
    mock_serialize.return_value = content_json
    m = Manifest()
    m._generation = 1

    m._save_gcs()

    assert mock_google_helper.return_value.upload_safe.call_count == 1


@patch('time.sleep')
@patch('platform_input_support.manifest.manifest.Manifest._refresh_from_gcs')
@patch('platform_input_support.manifest.manifest.Manifest._init_manifest')
@patch('platform_input_support.manifest.manifest.Manifest._serialize')
@patch('platform_input_support.manifest.manifest.google_helper')
def test_save_gcs_third_attempt(
    mock_google_helper,
    mock_serialize,
    mock_init_manifest,
    mock_refresh_from_gcs,
    mock_time_sleep,
):
    mock_google_helper.return_value.upload_safe.side_effect = [PreconditionFailedError, PreconditionFailedError, None]
    mock_serialize.return_value = content_json
    m = Manifest()
    m._generation = 1

    m._save_gcs()

    assert mock_google_helper.return_value.upload_safe.call_count == 3
    assert mock_time_sleep.call_count == 2


@patch('time.sleep')
@patch('platform_input_support.manifest.manifest.Manifest._refresh_from_gcs')
@patch('platform_input_support.manifest.manifest.Manifest._init_manifest')
@patch('platform_input_support.manifest.manifest.Manifest._serialize')
@patch('platform_input_support.manifest.manifest.google_helper')
def test_save_gcs_ko(
    mock_google_helper,
    mock_serialize,
    mock_init_manifest,
    mock_refresh_from_gcs,
    mock_time_sleep,
):
    mock_google_helper.return_value.upload_safe.side_effect = HelperError('test')
    mock_serialize.return_value = content_json
    m = Manifest()
    m._generation = 1

    with pytest.raises(PISCriticalError):
        m._save_gcs()

from pathlib import Path
from threading import Event
from unittest.mock import Mock, patch

import pytest

from platform_input_support.helpers.download import (
    DownloadHelper,
    GoogleSheetsDownloader,
    GoogleStorageDownloader,
    HelperError,
    HttpDownloader,
    TaskAbortedError,
    download,
)


@pytest.fixture
def download_helper():
    return DownloadHelper()


def test_get_protocol(download_helper):
    assert download_helper._get_protocol('https://example.com') == 'https'
    assert download_helper._get_protocol('http://example.com') == 'http'
    assert download_helper._get_protocol('gs://bucket/file') == 'gs'
    assert download_helper._get_protocol('https://docs.google.com/spreadsheets/d/123') == 'google_sheets'


@patch('platform_input_support.helpers.download.get_full_path')
@patch('platform_input_support.helpers.download.check_dir')
def test_prepare_destination(mock_check_dir, mock_get_full_path, download_helper):
    mock_get_full_path.return_value = Path('/full/path')

    result = download_helper._prepare_destination('/some/path')

    assert isinstance(result, Path)
    assert str(result) == '/full/path'
    mock_check_dir.assert_called_once()


@pytest.mark.parametrize(
    ('protocol', 'downloader_class'),
    [
        ('http', HttpDownloader),
        ('https', HttpDownloader),
        ('google_sheets', GoogleSheetsDownloader),
        ('gs', GoogleStorageDownloader),
    ],
)
def test_download_strategy_selection(download_helper, protocol, downloader_class):
    with patch.object(downloader_class, 'download') as mock_download:
        download_helper._prepare_destination = Mock(return_value=Path('/downloaded/file'))
        mock_download.return_value = Path('/downloaded/file')

        result = download_helper.download(f'{protocol}://example.com', '/dst')

        assert result == Path('/downloaded/file')
        mock_download.assert_called_once()


def test_download_unknown_protocol(download_helper):
    download_helper._prepare_destination = Mock(return_value=Path('/downloaded/file'))

    with pytest.raises(HelperError, match='unknown protocol ftp'):
        download_helper.download('ftp://example.com', '/dst')


@patch('platform_input_support.helpers.download.DownloadHelper.download')
def test_download_function(mock_download):
    mock_download.return_value = Path('/downloaded/file')

    result = download('https://example.com', '/dst')

    assert result == Path('/downloaded/file')
    mock_download.assert_called_once_with('https://example.com', '/dst', abort=None)


@patch('platform_input_support.helpers.download.requests.Session')
def test_http_downloader(mock_session):
    downloader = HttpDownloader()
    mock_session_instance = Mock()
    mock_session.return_value = mock_session_instance

    result = downloader.download('https://example.com', Path('/dst'))

    assert result == Path('/dst')
    mock_session_instance.mount.assert_called()
    mock_session_instance.get.assert_called_once_with('https://example.com', stream=True, timeout=(10, None))


@patch('platform_input_support.helpers.download.google_helper')
def test_google_sheets_downloader(mock_google_helper):
    downloader = GoogleSheetsDownloader()
    mock_session = Mock()
    mock_google_helper.return_value.get_session.return_value = mock_session

    result = downloader.download('https://docs.google.com/spreadsheets/d/123', Path('/dst'))

    assert result == Path('/dst')
    mock_google_helper.return_value.get_session.assert_called_once()
    mock_session.get.assert_called_once_with(
        'https://docs.google.com/spreadsheets/d/123', stream=True, timeout=(10, None)
    )


@patch('platform_input_support.helpers.download.google_helper')
def test_google_storage_downloader(mock_google_helper):
    downloader = GoogleStorageDownloader()
    result = downloader.download('gs://bucket/file', Path('/dst'))

    assert result == Path('/dst')
    mock_google_helper.return_value.download_to_file.assert_called_once_with('gs://bucket/file', Path('/dst'))


@patch('platform_input_support.helpers.download.open')
@patch('platform_input_support.helpers.download.shutil.copyfileobj')
@patch('platform_input_support.helpers.download.requests.Session')
def test_download_with_abort(mock_session, mock_copyfileobj, mock_open):
    downloader = HttpDownloader()
    mock_response = Mock()
    mock_session.return_value.get.return_value = mock_response
    mock_response.raise_for_status.return_value = None

    abort_event = Event()
    abort_event.set()  # Set the abort event

    mock_copyfileobj.side_effect = lambda *args: args[0].read(1, abort_event)  # Simulate reading the stream

    with pytest.raises(TaskAbortedError):
        downloader.download('https://example.com', Path('/dst'), abort=abort_event)

    mock_session.return_value.get.assert_called_once()
    mock_open.assert_called_once()
    mock_copyfileobj.assert_called_once()  # The copy should not complete due to the abort

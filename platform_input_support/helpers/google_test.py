from unittest.mock import MagicMock, patch

import pytest
from google.api_core.exceptions import GoogleAPICallError, PreconditionFailed
from google.cloud import storage
from google.cloud.exceptions import NotFound
from loguru import logger

from platform_input_support.helpers.google import GoogleHelper
from platform_input_support.util.errors import HelperError, NotFoundError, PreconditionFailedError

urls: list[tuple[str, tuple[str, str | None]]] = [
    ('gs://bucket/file.txt', ('bucket', 'file.txt')),
    ('gs://bucket', ('bucket', None)),
    ('gs://bucket/file.txt/extra', ('bucket', 'file.txt/extra')),
    ('bucket/file.txt', ('bucket', 'file.txt')),
    ('bucket', ('bucket', None)),
    ('bucket/file.txt/extra', ('bucket', 'file.txt/extra')),
    ('https://bucket/file.txt', ('bucket', 'file.txt')),
    ('https://bucket.storage.googleapis.com/folder/file.txt', ('bucket', 'folder/file.txt')),
]

test_list_input: list[str] = [
    'file_1.txt',
    'file_2.xls',
    'file_3.csv',
    'file_4.csv',
    'dir/file3.txt',
    'dir/file4.txt',
    'dir/deep/file5.txt',
    'dir/deep',
]

test_list_output: list[str] = [
    'file_1.txt',
    'file_2.txt',
    'file_3.csv',
    'file_4.csv',
]


@pytest.fixture(autouse=True)
def mock_init():
    with patch.object(GoogleHelper, '__init__', return_value=None) as mock_init:
        yield mock_init


@pytest.fixture
def mock_parse_url():
    with patch.object(GoogleHelper, '_parse_url', return_value=('bucket', 'file.txt')) as mock_parse_url:
        yield mock_parse_url


@pytest.mark.parametrize(
    ('input', 'expected'),
    [
        ('gs://bucket/file.txt', ('bucket', 'file.txt')),
        ('gs://bucket', ('bucket', None)),
        ('gs://bucket/file.txt/extra', ('bucket', 'file.txt/extra')),
        ('bucket/file.txt', ('bucket', 'file.txt')),
        ('bucket', ('bucket', None)),
        ('bucket/file.txt/extra', ('bucket', 'file.txt/extra')),
        ('https://bucket/file.txt', ('bucket', 'file.txt')),
        ('https://bucket.storage.googleapis.com/folder/file.txt', ('bucket', 'folder/file.txt')),
    ],
)
def test_parse_url(input, expected):
    assert GoogleHelper._parse_url(input) == expected


@pytest.mark.parametrize(
    'input',
    [
        'bucket$',
        'BUCKET',
        'bucket-',
        '-bucket',
        'bu',
    ],
)
def test_parse_bad_buckets(input):
    with pytest.raises(HelperError):
        GoogleHelper._parse_url(input)


def test_get_bucket_existing(mock_parse_url):
    g = GoogleHelper()
    g.client = MagicMock(storage.Client)

    g._get_bucket('bucket')

    g.client.get_bucket.assert_called_once_with('bucket')


def test_get_bucket_non_existent(mock_parse_url):
    g = GoogleHelper()
    g.client = MagicMock(storage.Client)
    g.client.get_bucket.side_effect = NotFound('test')

    with pytest.raises(NotFoundError):
        g._get_bucket('gs://bucket')


def test_get_bucket_ko(mock_parse_url):
    g = GoogleHelper()
    g.client = MagicMock(storage.Client)
    g.client.get_bucket.side_effect = GoogleAPICallError('test')

    with pytest.raises(HelperError):
        g._get_bucket('gs://bucket')


def test_prepare_blob_existing(mock_parse_url):
    g = GoogleHelper()
    g.client = MagicMock(storage.Client)
    bucket = MagicMock(storage.Bucket)

    b = g._prepare_blob(bucket, 'file.txt')

    bucket.blob.assert_called_once_with('file.txt')
    assert b == bucket.blob.return_value


def test_prepare_blob_non_existing(mock_parse_url):
    g = GoogleHelper()
    g.client = MagicMock(storage.Client)
    bucket = MagicMock(storage.Bucket)
    bucket.blob.side_effect = NotFoundError('test')

    with pytest.raises(NotFoundError):
        g._prepare_blob(bucket, 'gs://bucket/file.txt')


def test_prepare_blob_ko(mock_parse_url):
    g = GoogleHelper()
    g.client = MagicMock(storage.Client)
    bucket = MagicMock(storage.Bucket)
    bucket.blob.side_effect = GoogleAPICallError('test')

    with pytest.raises(HelperError):
        g._prepare_blob(bucket, 'gs://bucket/file.txt')


def test_download_to_string_ok(mock_parse_url):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.download_as_string.return_value = b'test'
    g._prepare_blob.return_value.generation = 123

    g.download_to_string('gs://bucket/file.txt')

    assert g.download_to_string('gs://bucket/file.txt') == ('test', 123)


def test_download_to_string_not_found(mock_parse_url):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.download_as_string.side_effect = NotFound('test')

    with pytest.raises(NotFoundError):
        g.download_to_string('gs://bucket/file.txt')


def test_download_to_string_decode_error(mock_parse_url):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.download_as_string.return_value = b'\x80'

    with pytest.raises(HelperError):
        g.download_to_string('gs://bucket/file.txt')


def test_download_to_file_ok(mock_parse_url, tmp_path):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    destination = tmp_path / 'file.txt'

    g.download_to_file('gs://bucket/file.txt', destination)

    g._prepare_blob.return_value.download_to_filename.assert_called_once_with(destination)


def test_download_to_file_not_found(mock_parse_url, tmp_path):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.download_to_filename.side_effect = NotFound('test')
    destination = tmp_path / 'file.txt'

    with pytest.raises(NotFoundError):
        g.download_to_file('gs://bucket/file.txt', destination)


def test_download_to_file_ko(mock_parse_url, tmp_path):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.download_to_filename.side_effect = [GoogleAPICallError('test'), OSError('test')]
    destination = tmp_path / 'file.txt'

    with pytest.raises(HelperError):
        g.download_to_file('gs://bucket/file.txt', destination)

    with pytest.raises(HelperError):
        g.download_to_file('gs://bucket/file.txt', destination)


def test_upload_safe_ok(mock_parse_url):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()

    g.upload_safe('data', 'gs://bucket/file.txt', 123)

    g._prepare_blob.return_value.upload_from_string.assert_called_once_with('data', if_generation_match=123)


def test_upload_safe_precondition_failed(mock_parse_url):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.upload_from_string.side_effect = PreconditionFailed('test')

    with pytest.raises(PreconditionFailedError):
        g.upload_safe('data', 'gs://bucket/file.txt', 123)


def test_upload_safe_ko(mock_parse_url):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.upload_from_string.side_effect = [GoogleAPICallError('test'), OSError('test')]

    with pytest.raises(HelperError):
        g.upload_safe('data', 'gs://bucket/file.txt', 123)

    with pytest.raises(HelperError):
        g.upload_safe('data', 'gs://bucket/file.txt', 123)


@pytest.mark.parametrize(
    ('blob_name', 'prefix', 'result'),
    [
        ('file.txt', None, True),
        ('file.txt', '', True),
        ('file.txt', '/', True),
        ('file', None, True),
        ('file', '', True),
        ('prefix/file.txt', 'prefix/', True),
        ('prefix/file.txt', 'prefix', True),
        ('/prefix/file.txt', '/prefix/', True),
        ('/prefix/file.txt', '/prefix', True),
        ('/prefix/file.txt', 'prefix/', False),
        ('/dir/', None, False),
        ('/dir/', '', False),
        ('/dir/', '/dir', False),
        ('prefix/dir/', '/prefix', False),
        ('/dir/file.txt', '', False),
        ('/prefix/dir/file.txt', '/prefix/', False),
        ('', '', False),
        ('/', '', False),
    ],
)
def test_is_blob_shallow(blob_name, prefix, result):
    assert GoogleHelper._is_blob_shallow(blob_name, prefix) == result


def test_list_blobs_returns_some_files(mock_parse_url):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._get_bucket.return_value.list_blobs.return_value = [storage.Blob(n, 't') for n in test_list_input]

    blob_names = g.list_blobs('testpath')

    assert len(blob_names) == len(test_list_output)


def test_list_returns_no_files(mock_parse_url, caplog):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._get_bucket.return_value.list_blobs.return_value = []
    logger.add(caplog.handler, level='TRACE', format='{message}')

    blob_names = g.list_blobs('testpath')

    assert 'no files found in testpath' in caplog.text
    assert len(blob_names) == 0


def test_list_include_files(mock_parse_url):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._get_bucket.return_value.list_blobs.return_value = [storage.Blob(n, 't') for n in test_list_input]

    blob_names = g.list_blobs('testpath', include='csv')

    assert len(blob_names) == 2


def test_list_include_exclude(mock_parse_url):
    g = GoogleHelper()
    g._get_bucket = MagicMock()
    g._get_bucket.return_value.list_blobs.return_value = [storage.Blob(n, 't') for n in test_list_input]

    blob_names = g.list_blobs('testpath', exclude='txt')

    assert len(blob_names) == 3

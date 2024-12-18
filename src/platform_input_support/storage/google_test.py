from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from google.api_core.exceptions import GoogleAPICallError, PreconditionFailed
from google.cloud import storage
from google.cloud.exceptions import NotFound
from loguru import logger

from platform_input_support.storage.google import GoogleStorage
from platform_input_support.util.errors import NotFoundError, PreconditionFailedError, StorageError

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
    with patch.object(GoogleStorage, '__init__', return_value=None) as mock_init:
        yield mock_init


@pytest.fixture
def mock_parse_url():
    with patch.object(GoogleStorage, '_parse_uri', return_value=('bucket', 'file.txt')) as mock_parse_url:
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
    ],
)
def test_parse_uri_ok(input, expected):
    assert GoogleStorage._parse_uri(input) == expected


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
def test_parse_uri_ko(input):
    with pytest.raises(StorageError):
        GoogleStorage._parse_uri(input)


def test_get_bucket_ok(mock_parse_url):
    g = GoogleStorage()
    g.client = MagicMock(storage.Client)

    g._get_bucket('bucket')

    g.client.get_bucket.assert_called_once_with('bucket')


def test_get_bucket_ko(mock_parse_url):
    g = GoogleStorage()
    g.client = MagicMock(storage.Client)
    g.client.get_bucket.side_effect = GoogleAPICallError('test')

    with pytest.raises(StorageError):
        g._get_bucket('gs://bucket')

    g.client.get_bucket.side_effect = Exception('test')

    with pytest.raises(StorageError):
        g._get_bucket('gs://bucket')


def test_get_bucket_non_existing(mock_parse_url):
    g = GoogleStorage()
    g.client = MagicMock(storage.Client)
    g.client.get_bucket.side_effect = NotFound('test')

    with pytest.raises(NotFoundError):
        g._get_bucket('gs://bucket')


def test_prepare_blob_ok(mock_parse_url):
    g = GoogleStorage()
    g.client = MagicMock(storage.Client)
    bucket = MagicMock(storage.Bucket)

    b = g._prepare_blob(bucket, 'file.txt')

    bucket.blob.assert_called_once_with('file.txt')
    assert b == bucket.blob.return_value


def test_prepare_blob_ko(mock_parse_url):
    g = GoogleStorage()
    g.client = MagicMock(storage.Client)
    bucket = MagicMock(storage.Bucket)
    bucket.blob.side_effect = GoogleAPICallError('test')

    with pytest.raises(StorageError):
        g._prepare_blob(bucket, 'gs://bucket/file.txt')


def test_prepare_blob_non_existing(mock_parse_url):
    g = GoogleStorage()
    g.client = MagicMock(storage.Client)
    bucket = MagicMock(storage.Bucket)
    bucket.blob.side_effect = NotFoundError('test')

    with pytest.raises(NotFoundError):
        g._prepare_blob(bucket, 'gs://bucket/file.txt')


def test_prepare_blob_no_prefix(mock_parse_url):
    g = GoogleStorage()
    g.client = MagicMock(storage.Client)
    bucket = MagicMock(storage.Bucket)
    bucket.blob.side_effect = GoogleAPICallError('test')

    with pytest.raises(StorageError):
        g._prepare_blob(bucket, None)


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
    assert GoogleStorage._is_blob_shallow(blob_name, prefix) == result


def test_check_ok(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._get_bucket.return_value.test_iam_permissions = MagicMock(
        return_value=[
            'storage.buckets.get',
            'storage.objects.list',
            'storage.objects.get',
            'storage.objects.create',
            'storage.objects.delete',
            'storage.objects.update',
        ]
    )

    assert g.check('gs://bucket')


def test_check_ko(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._get_bucket.return_value.test_iam_permissions = MagicMock(return_value=[])

    assert not g.check('gs://bucket')


def test_check_non_existing(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._get_bucket.side_effect = NotFoundError('test')

    assert not g.check('gs://bucket')


def test_stat_ok(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.updated = datetime(2021, 1, 1)

    assert g.stat('gs://bucket/file.txt') == ({'mtime': datetime(2021, 1, 1).timestamp()})
    assert g._prepare_blob.return_value.reload.called


def test_stat_ko(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.reload.side_effect = GoogleAPICallError('test')

    with pytest.raises(StorageError):
        g.stat('gs://bucket/file.txt')


def test_stat_non_existing(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.reload.side_effect = NotFound('test')

    with pytest.raises(NotFoundError):
        g.stat('gs://bucket/file.txt')


def test_list_blobs_ok(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._get_bucket.return_value.list_blobs.return_value = [storage.Blob(n, 't') for n in test_list_input]

    blob_names = g.list('testpath')

    assert len(blob_names) == len(test_list_output)


def test_list_ok_empty(mock_parse_url, caplog):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._get_bucket.return_value.list_blobs.return_value = []
    logger.add(caplog.handler, level='TRACE', format='{message}')

    blob_names = g.list('testpath')

    assert 'no files found in testpath' in caplog.text
    assert len(blob_names) == 0


def test_list_ok_pattern(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._get_bucket.return_value.list_blobs.return_value = [storage.Blob(n, 't') for n in test_list_input]

    blob_names = g.list('testpath', pattern='csv')

    assert len(blob_names) == 2


def test_list_ok_negative_pattern(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._get_bucket.return_value.list_blobs.return_value = [storage.Blob(n, 't') for n in test_list_input]

    blob_names = g.list('testpath', pattern='!txt')

    assert len(blob_names) == 3


def test_download_to_file_ok(mock_parse_url, tmp_path):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    destination = tmp_path / 'file.txt'
    g._prepare_blob.return_value.generation = 123123123

    assert g.download_to_file('gs://bucket/file.txt', destination) == 123123123
    g._prepare_blob.return_value.download_to_filename.assert_called_once_with(destination)


def test_download_to_file_not_found(mock_parse_url, tmp_path):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.download_to_filename.side_effect = NotFound('test')
    destination = tmp_path / 'file.txt'

    with pytest.raises(NotFoundError):
        g.download_to_file('gs://bucket/file.txt', destination)


def test_download_to_file_ko(mock_parse_url, tmp_path):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.download_to_filename.side_effect = [GoogleAPICallError('test'), OSError('test')]
    destination = tmp_path / 'file.txt'

    with pytest.raises(StorageError):
        g.download_to_file('gs://bucket/file.txt', destination)


def test_download_to_string_ok(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.download_as_string.return_value = b'test'
    g._prepare_blob.return_value.generation = 123

    g.download_to_string('gs://bucket/file.txt')

    assert g.download_to_string('gs://bucket/file.txt') == ('test', 123)


def test_download_to_string_not_found(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.download_as_string.side_effect = NotFound('test')

    with pytest.raises(NotFoundError):
        g.download_to_string('gs://bucket/file.txt')


def test_download_to_string_decode_error(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.download_as_string.return_value = b'\x80'

    with pytest.raises(StorageError):
        g.download_to_string('gs://bucket/file.txt')


def test_upload_ok(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    src = Path('file.txt')

    g.upload(src, 'gs://bucket/file.txt')

    g._prepare_blob.return_value.upload_from_filename.assert_called_once_with(src)


def test_upload_ok_revision(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    src = Path('file.txt')
    r = 123123

    g.upload(src, 'gs://bucket/file.txt', r)

    g._prepare_blob.return_value.upload_from_filename.assert_called_once_with(src, if_generation_match=r)


def test_upload_ko(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.upload_from_filename.side_effect = [GoogleAPICallError('test'), OSError('test')]
    src = Path('file.txt')

    with pytest.raises(StorageError):
        g.upload(src, 'gs://bucket/file.txt', 123)


def test_upload_ko_bad_revision(mock_parse_url):
    g = GoogleStorage()
    g._get_bucket = MagicMock()
    g._prepare_blob = MagicMock()
    g._prepare_blob.return_value.upload_from_filename.side_effect = PreconditionFailed('test')
    src = Path('file.txt')

    with pytest.raises(PreconditionFailedError):
        g.upload(src, 'gs://bucket/file.txt', 123)

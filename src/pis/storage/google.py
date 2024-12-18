"""Google Cloud Storage helper module."""

import re
import sys
from datetime import datetime
from pathlib import Path

from google import auth
from google.api_core.exceptions import GoogleAPICallError, PreconditionFailed
from google.auth import exceptions as auth_exceptions
from google.auth.transport.requests import AuthorizedSession
from google.cloud import storage
from google.cloud.exceptions import NotFound
from loguru import logger

from pis.helpers import RemoteStorage
from pis.util.errors import NotFoundError, PreconditionFailedError, StorageError

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/spreadsheets',
]


class GoogleStorage(RemoteStorage):
    """Google Cloud Storage helper class.

    This class implements the RemoteStorage interface for Google Cloud Storage.

    :ivar credentials: The Google Cloud Storage credentials.
    :vartype credentials: google.auth.credentials.Credentials
    :ivar client: The Google Cloud Storage client.
    :vartype client: google.cloud.storage.client.Client
    """

    def __init__(self):
        try:
            credentials, project_id = auth.default(scopes=GOOGLE_SCOPES)
            logger.debug(f'gcp authenticated on project {project_id}')
        except auth_exceptions.DefaultCredentialsError as e:
            logger.critical(f'error authenticating on gcp: {e}')
            sys.exit(1)

        self.credentials = credentials
        self.client = storage.Client(credentials=credentials)

    @classmethod
    def _parse_uri(cls, uri: str) -> tuple[str, str | None]:
        uri_parts = uri.replace('gs://', '').split('/', 1)
        bucket_name = uri_parts[0]

        bucket_re = r'^[a-z0-9][a-z0-9-_.]{2,221}[a-z0-9]$'
        if re.match(bucket_re, bucket_name) is None:
            raise StorageError(f'invalid bucket name: {bucket_name}')

        file_path = uri_parts[1] if len(uri_parts) > 1 else None
        return bucket_name, file_path

    def _get_bucket(self, bucket_name: str) -> storage.Bucket:
        try:
            return self.client.get_bucket(bucket_name)
        except NotFound:
            raise NotFoundError(bucket_name)
        except GoogleAPICallError as e:
            raise StorageError(f'google api error checking bucket {bucket_name}: {e}')
        except Exception as e:
            raise StorageError(f'error checking bucket {bucket_name}: {e}')

    def _prepare_blob(self, bucket: storage.Bucket, prefix: str | None) -> storage.Blob:
        if prefix is None:
            raise StorageError(f'invalid prefix: {prefix}')
        try:
            blob = bucket.blob(prefix)
        except GoogleAPICallError as e:
            raise StorageError(f'error preparing blob: {e}')
        return blob

    @staticmethod
    def _is_blob_shallow(blob_name: str, prefix: str | None) -> bool:
        # make sure we select the given path, not all prefixes
        if prefix is not None and not prefix.endswith('/'):
            prefix = f'{prefix}/'

        if not blob_name or blob_name == prefix:
            return False

        blob_name = blob_name.replace(prefix or '', '', 1)
        return '/' not in blob_name and not blob_name.endswith('/')

    def check(self, uri: str) -> bool:
        """Check if a bucket exists in Google Cloud Storage.

        :param uri: The URI of the file to check.
        :type uri: str
        :return: True if the file exists, False otherwise.
        :rtype: bool
        """
        bucket_name, _ = self._parse_uri(uri)
        bucket = None
        permissions = [
            'storage.buckets.get',
            'storage.objects.list',
            'storage.objects.get',
            'storage.objects.create',
            'storage.objects.delete',
            'storage.objects.update',
        ]

        try:
            bucket = self._get_bucket(bucket_name)
        except NotFoundError:
            logger.warning(f'bucket {bucket_name} not found')
            return False

        actual_permissions = bucket.test_iam_permissions(permissions)

        if actual_permissions != permissions:
            missing_permissions = ', '.join(set(permissions) - set(actual_permissions))
            logger.warning(f'bucket {bucket_name} exists but is missing {missing_permissions} permission')
            return False

        logger.debug(f'bucket {bucket_name} exists and is readable')
        return True

    def stat(self, uri: str) -> dict:
        """Get metadata for a file in Google Cloud Storage.

        :param uri: The URI of the file to get metadata for.
        :type uri: str
        :return: A dictionary containing metadata.
        :rtype: dict
        :raises NotFoundError: If the file does not exist.
        """
        bucket_name, prefix = self._parse_uri(uri)
        bucket = self._get_bucket(bucket_name)
        blob = self._prepare_blob(bucket, prefix)

        try:
            blob.reload()
        except NotFound:
            raise NotFoundError(uri)
        except GoogleAPICallError as e:
            raise StorageError(f'error getting metadata for {uri}: {e}')
        return {'mtime': datetime.timestamp(blob.updated) if blob.updated else None}

    def list(self, uri: str, pattern: str | None = None) -> list[str]:
        """List blobs in a bucket.

        :param uri: The URI prefix to list blobs for.
        :type uri: str
        :param pattern: The pattern to match blobs against.
        :type pattern: str | None
        :return: A list of blob URIs.
        :rtype: list[str]
        :raises NotFoundError: If the bucket or prefix does not exist.
        :raises StorageError: If the prefix is invalid.
        """
        bucket_name, prefix = self._parse_uri(uri)
        bucket = self._get_bucket(bucket_name)
        blob_names: list[str] = [n.name for n in list(bucket.list_blobs(prefix=prefix))]

        # filter out blobs that have longer prefixes
        blob_name_list = [n for n in blob_names if self._is_blob_shallow(n, prefix)]
        # filter out blobs using include/exclude
        if pattern is not None:
            if pattern.startswith('!'):
                blob_name_list = [blob_name for blob_name in blob_name_list if pattern[1:] not in blob_name]
            else:
                blob_name_list = [blob_name for blob_name in blob_name_list if pattern in blob_name]

        if len(blob_name_list) == 0:
            logger.warning(f'no files found in {uri}')

        return [f'gs://{bucket_name}/{blob_name}' for blob_name in blob_name_list]

    def download_to_file(self, uri: str, dst: Path) -> int:
        """Download a file from Google Cloud Storage to the local filesystem.

        :param uri: The URI of the file to download.
        :type uri: str
        :param dst: The destination path to download the file to.
        :type dst: Path
        :return: The generation number of the file.
        :rtype: int
        :raises NotFoundError: If the file is not found.
        :raises StorageError: If an error occurs while downloading the file.
        """
        bucket_name, prefix = self._parse_uri(uri)
        bucket = self._get_bucket(bucket_name)
        blob = self._prepare_blob(bucket, prefix)

        try:
            blob.download_to_filename(dst)
        except NotFound:
            raise NotFoundError(uri)
        except (GoogleAPICallError, OSError) as e:
            raise StorageError(f'error downloading {uri}: {e}')
        return blob.generation or 0

    def download_to_string(self, uri: str) -> tuple[str, int]:
        """Download a file from Google Cloud Storage and return its contents as a string.

        :param uri: The URI of the file to download.
        :type uri: str
        :raises NotFoundError: If the file is not found.
        :raises StorageError: If an error occurs while downloading the file.
        :return: A tuple containing the file contents and the generation number.
        :rtype: tuple[str, int]
        """
        bucket_name, prefix = self._parse_uri(uri)
        bucket = self._get_bucket(bucket_name)
        blob = self._prepare_blob(bucket, prefix)

        try:
            blob_str = blob.download_as_string()
        except NotFound:
            raise NotFoundError(f'file {uri} not found')

        decoded_blob = None
        try:
            decoded_blob = blob_str.decode('utf-8')
        except UnicodeDecodeError as e:
            raise StorageError(f'error decoding file {uri}: {e}')
        assert blob.generation is not None
        return (decoded_blob, blob.generation)

    def upload(self, src: Path, uri: str, revision: int | None = None) -> int:
        """Upload a file to Google Cloud Storage.

        :param src: The source path of the file to upload.
        :type src: Path
        :param uri: The URI to upload the file to.
        :type uri: str
        :param revision: The expected revision number of the file.
        :type revision: int | None
        :return: The new revision number of the file.
        :rtype: int
        :raises StorageError: If an error occurs during upload.
        :raises PreconditionFailedError: If the revision number does not match.
        """
        bucket_name, prefix = self._parse_uri(uri)
        bucket = self._get_bucket(bucket_name)
        blob = self._prepare_blob(bucket, prefix)

        try:
            if revision is not None:
                blob.upload_from_filename(src, if_generation_match=revision)
            else:
                blob.upload_from_filename(src)
        except PreconditionFailed:
            raise PreconditionFailedError(f'upload of {src} failed due to generation mismatch')
        except (GoogleAPICallError, OSError) as e:
            raise StorageError(f'error uploading {src}: {e}')
        blob.reload()
        return blob.generation or 0

    def get_session(self) -> AuthorizedSession:
        """Get the current authenticated session.

        :return: An authorized session.
        :rtype: AuthorizedSession
        """
        return AuthorizedSession(self.credentials)

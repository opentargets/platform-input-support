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

from platform_input_support.config import settings
from platform_input_support.util.errors import HelperError, NotFoundError, PreconditionFailedError

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/spreadsheets',
]


class GoogleHelper:
    def __init__(self):
        try:
            credentials, project_id = auth.default(scopes=GOOGLE_SCOPES)
            logger.debug(f'gcp authenticated on project {project_id}')
        except auth_exceptions.DefaultCredentialsError as e:
            logger.critical(f'error authenticating on gcp: {e}')
            sys.exit(1)

        self.credentials = credentials
        self.client = storage.Client(credentials=credentials)
        self.is_ready = False

        if settings().gcs_url is None:
            logger.warning('gcs_url setting and PIS_GCS_URL env var are missing')
            return

        # check if the bucket exists
        try:
            if not self.bucket_exists(settings().gcs_url):
                logger.critical(f'{settings().gcs_url} does not exist')
                sys.exit(1)
        except HelperError as e:
            logger.critical(f'error checking google cloud storage url: {e}')
            sys.exit(1)

        # if the credentials are good and the bucket exists, the google helper is ready
        self.is_ready = True

    @classmethod
    def _parse_url(cls, url: str) -> tuple[str, str | None]:
        if url.startswith('http'):
            url = url.replace('https://', '').replace('http://', '').replace('.storage.googleapis.com', '')

        url_parts = url.replace('gs://', '').split('/', 1)
        bucket_name = url_parts[0]

        bucket_re = r'^[a-z0-9][a-z0-9-_.]{2,221}[a-z0-9]$'
        if re.match(bucket_re, bucket_name) is None:
            raise HelperError(f'invalid bucket name: {bucket_name}')

        file_path = url_parts[1] if len(url_parts) > 1 else None
        return bucket_name, file_path

    def _get_bucket(self, bucket_name: str) -> storage.Bucket:
        try:
            return self.client.get_bucket(bucket_name)
        except NotFound:
            raise NotFoundError(bucket_name)
        except GoogleAPICallError as e:
            raise HelperError(f'google api error checking bucket {bucket_name}: {e}')
        except Exception as e:
            raise HelperError(f'error checking bucket {bucket_name}: {e}')

    def _prepare_blob(self, bucket: storage.Bucket, prefix: str | None) -> storage.Blob:
        if prefix is None:
            raise HelperError(f'invalid prefix: {prefix}')
        try:
            blob = bucket.blob(prefix)
        except GoogleAPICallError as e:
            raise HelperError(f'error preparing blob: {e}')
        return blob

    def bucket_exists(self, url: str) -> bool:
        bucket_name, _ = self._parse_url(url)
        try:
            self._get_bucket(bucket_name)
        except NotFoundError:
            logger.warning(f'bucket {bucket_name} not found')
            return False
        logger.debug(f'bucket {bucket_name} exists and is readable')
        return True

    def download_to_string(self, url: str) -> tuple[str, int] | None:
        bucket_name, prefix = self._parse_url(url)
        bucket = self._get_bucket(bucket_name)
        blob = self._prepare_blob(bucket, prefix)

        try:
            blob_str = blob.download_as_string()
        except NotFound:
            logger.warning(f'file {url} not found')
            raise NotFoundError(f'file {url} not found')

        decoded_blob = None
        try:
            decoded_blob = blob_str.decode('utf-8')
        except UnicodeDecodeError as e:
            raise HelperError(f'error decoding file {url}: {e}')
        assert blob.generation is not None
        return (decoded_blob, blob.generation)

    def download_to_file(self, url: str, destination: Path) -> None:
        bucket_name, prefix = self._parse_url(url)
        bucket = self._get_bucket(bucket_name)
        blob = self._prepare_blob(bucket, prefix)

        try:
            blob.download_to_filename(destination)
        except NotFound:
            raise NotFoundError(url)
        except (GoogleAPICallError, OSError) as e:
            raise HelperError(f'error downloading {url}: {e}')
        logger.debug('download completed')

    def upload(self, source: Path, destination: str) -> None:
        bucket_name, prefix = self._parse_url(destination)
        bucket = self._get_bucket(bucket_name)
        blob = self._prepare_blob(bucket, prefix)

        try:
            blob.upload_from_filename(source)
        except (GoogleAPICallError, OSError) as e:
            raise HelperError(f'error uploading {source}: {e}')
        logger.debug(f'uploaded {source} to {destination}')

    def upload_safe(self, content: str, destination: str, generation: int) -> None:
        bucket_name, prefix = self._parse_url(destination)
        bucket = self._get_bucket(bucket_name)
        blob = self._prepare_blob(bucket, prefix)

        logger.trace(f'uploading file with generation {generation}')
        try:
            blob.upload_from_string(content, if_generation_match=generation)
        except PreconditionFailed:
            logger.trace('file upload failed due to generation mismatch')
            blob.reload()
            raise PreconditionFailedError(f'generation mismatch: local={generation}, remote={blob.generation}')
        except (GoogleAPICallError, OSError) as e:
            raise HelperError(f'error uploading file to {destination}: {e}')

        logger.debug(f'uploaded blob to {destination}')

    @staticmethod
    def _is_blob_shallow(blob_name: str, prefix: str | None) -> bool:
        # make sure we select the given path, not all prefixes
        if prefix is not None and not prefix.endswith('/'):
            prefix = f'{prefix}/'

        if not blob_name or blob_name == prefix:
            return False

        blob_name = blob_name.replace(prefix or '', '', 1)
        return '/' not in blob_name and not blob_name.endswith('/')

    def list(self, url: str, include: str | None = None, exclude: str | None = None) -> list[str]:
        bucket_name, prefix = self._parse_url(url)
        bucket = self._get_bucket(bucket_name)

        blob_names: list[str] = [n.name for n in list(bucket.list_blobs(prefix=prefix))]

        # filter out blobs that have longer prefixes
        blob_name_list = [n for n in blob_names if self._is_blob_shallow(n, prefix)]

        # filter out blobs using include/exclude
        if include is not None:
            blob_name_list = [blob_name for blob_name in blob_name_list if include in blob_name]
        elif exclude is not None:
            blob_name_list = [blob_name for blob_name in blob_name_list if exclude not in blob_name]

        if len(blob_name_list) == 0:
            logger.warning(f'no files found in {url}')

        return [f'gs://{bucket_name}/{blob_name}' for blob_name in blob_name_list]

    def get_modification_date(self, url: str) -> datetime | None:
        bucket_name, prefix = self._parse_url(url)
        bucket = self._get_bucket(bucket_name)
        blob = self._prepare_blob(bucket, prefix)
        blob.reload()
        return blob.updated

    def get_session(self) -> AuthorizedSession:
        return AuthorizedSession(self.credentials)

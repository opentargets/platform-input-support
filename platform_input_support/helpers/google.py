import datetime
import sys
from pathlib import Path

from google import auth
from google.api_core.exceptions import GoogleAPICallError
from google.auth import exceptions as auth_exceptions
from google.auth.transport.requests import AuthorizedSession
from google.cloud import storage
from google.cloud.exceptions import NotFound
from loguru import logger

from platform_input_support.config import settings
from platform_input_support.util.errors import HelperError, NotFoundError

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/spreadsheets',
]


class GoogleHelper:
    def __init__(self):
        try:
            credentials, project_id = auth.default(scopes=GOOGLE_SCOPES)
            logger.debug(f'gcp authenticated on project `{project_id}`')
        except auth_exceptions.DefaultCredentialsError as e:
            logger.critical(f'error authenticating on gcp: {e}')
            sys.exit(1)

        self.credentials = credentials
        self.client = storage.Client(credentials=credentials)
        self.is_ready = False

        if settings.gcs_url is None:
            logger.warning('`gcs_url` setting and `PIS_GCS_URL` env var are missing')
            return

        # check if the configured bucket exists
        try:
            if not self.bucket_exists(settings.gcs_url):
                logger.critical(f'`{settings.gcs_url}` does not exist')
                sys.exit(1)
        except HelperError as e:
            logger.critical(f'error checking google cloud storage url: {e}')
            sys.exit(1)

        # if the credentials are good and the bucket exists, the google helper is ready
        self.is_ready = True

    @staticmethod
    def _parse_url(url: str) -> tuple[str, str | None]:
        url_parts = url.replace('gs://', '').split('/', 1)
        bucket_name = url_parts[0]
        file_path = url_parts[1] if len(url_parts) > 1 else None
        return bucket_name, file_path

    def bucket_exists(self, url: str) -> bool:
        bucket_name, _ = self._parse_url(url)

        try:
            self.client.get_bucket(bucket_name)
        except NotFound:
            logger.warning(f'bucket `{bucket_name}` not found')
            return False
        except GoogleAPICallError as e:
            raise HelperError(f'error checking bucket: {e}')

        logger.debug(f'bucket `{bucket_name}` exists and is readable')
        return True

    def download(self, url: str, destination: Path | None = None) -> str | None:
        bucket_name, file_path = self._parse_url(url)

        try:
            bucket = self.client.get_bucket(bucket_name)
        except NotFound:
            raise NotFoundError(bucket_name)

        blob = bucket.blob(file_path)

        if destination is None:
            try:
                blob_str = blob.download_as_string()
            except NotFound:
                # downloading to memory is used for the manifest
                # we do not panic if the file is not there
                logger.warning(f'file `{url}` not found')
                return None

            try:
                decoded_blob = blob_str.decode('utf-8')
            except UnicodeDecodeError as e:
                raise HelperError(f'error decoding file `{url}`: {e}')

            logger.debug(f'downloaded `{url}`')
            return decoded_blob

        else:
            try:
                blob.download_to_filename(destination)
            except NotFound:
                raise NotFoundError(url)
            except GoogleAPICallError as e:
                raise HelperError(f'error downloading file: {e}')
            except OSError as e:
                raise HelperError(f'error writing file: {e}')

            logger.debug(f'downloaded `{url}` to `{destination}`')

    def upload(self, source: str, destination: str):
        bucket_name, file_path = self._parse_url(destination)

        try:
            bucket = self.client.get_bucket(bucket_name)
        except NotFound:
            raise NotFoundError(bucket_name)

        blob = bucket.blob(file_path)

        try:
            blob.upload_from_filename(source)
        except GoogleAPICallError as e:
            raise HelperError(f'error uploading file: {e}')
        except OSError as e:
            raise HelperError(f'error reading file: {e}')

        logger.debug(f'uploaded `{source}` to `{destination}`')

    @staticmethod
    def _is_file(blob: storage.Blob, prefix: str | None) -> bool:
        blob_name = str(blob.name).replace(prefix or '', '')
        return '/' not in blob_name and not blob_name.endswith('/')

    def list(self, url: str, include: str | None = None, exclude: str | None = None) -> list[str]:
        bucket_name, prefix = self._parse_url(url)

        # make sure we select the given path, not all prefixes
        if prefix is not None and not prefix.endswith('/'):
            prefix = f'{prefix}/'

        file_list = []
        try:
            bucket = self.client.get_bucket(bucket_name)
        except NotFound:
            raise NotFoundError(bucket_name)
        except GoogleAPICallError as e:
            raise HelperError(f'error getting bucket: {e}')

        blobs = list(bucket.list_blobs(prefix=prefix))

        # filter out blobs that have longer prefixes
        file_list = [blob for blob in blobs if self._is_file(blob, prefix)]

        # filter out blobs using include/exclude
        if include is not None:
            file_list = [blob for blob in file_list if include in blob.name]
        elif exclude is not None:
            file_list = [blob for blob in file_list if exclude not in blob.name]

        if not file_list:
            logger.warning(f'no files found in `{url}`')
            return []

        return [f'gs://{bucket_name}/{blob.name}' for blob in file_list]

    def get_modification_date(self, url: str) -> datetime.datetime | None:
        bucket_name, file_path = self._parse_url(url)

        try:
            bucket = self.client.get_bucket(bucket_name)
        except NotFound:
            raise NotFoundError(f'bucket or file `{url}` not found')
        except GoogleAPICallError as e:
            raise HelperError(f'error getting creation date: {e}')

        blob = bucket.blob(file_path)
        blob.reload()
        return blob.updated

    def get_session(self) -> AuthorizedSession:
        return AuthorizedSession(self.credentials)

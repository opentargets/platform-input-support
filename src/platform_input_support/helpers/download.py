"""Helper that downloads files from various sources."""

import functools
import shutil
from pathlib import Path
from threading import Event

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from platform_input_support.helpers import google_helper
from platform_input_support.util.errors import HelperError, TaskAbortedError
from platform_input_support.util.fs import absolute_path, check_fs

# we are going to download big files, better to use a big chunk size
CHUNK_SIZE = 1024 * 1024 * 10
REQUEST_TIMEOUT = 10


class AbortableStreamWrapper:
    """A wrapper around a stream that can be aborted.

    This class wraps a stream and in every read operation, it will raise a
    :class:`platform_input_support.util.errors.TaskAbortedError` if the abort event
    is set. This is useful to abort downloads when another task fails.
    """

    def __init__(self, stream, *, abort: Event):
        self.stream = stream
        self.abort = abort

    def read(self, *args, **kwargs) -> bytes:
        """Read from the stream and raise TaskAbortedError if the abort event is set.

        :return: The data read from the stream.
        :rtype: bytes
        :raises TaskAbortedError: If the abort event is set.
        """
        if self.abort and self.abort.is_set():
            raise TaskAbortedError
        return self.stream.read(*args, **kwargs)


class Downloader:
    """Base class for downloaders."""

    def download(self, src: str, dst: Path, *, abort: Event | None = None) -> Path:
        """Download a file from a source to a destination.

        This method is a no-op and should be overridden by subclasses.

        :param src: The source URL.
        :type src: str
        :param dst: The destination path.
        :type dst: Path
        :param abort: An event that can be set to abort the download, defaults to `None`
        :type abort: Event | None, optional
        :return: The destination path.
        :rtype: Path
        """
        return dst

    @staticmethod
    def _download(src: str, dst: Path, s: requests.Session, abort: Event | None = None):
        r = s.get(src, stream=True, timeout=(REQUEST_TIMEOUT, None))
        r.raise_for_status()

        if abort:
            # Wrap r.raw with an AbortableStreamWrapper
            abortable_stream = AbortableStreamWrapper(r.raw, abort=abort)
            # Ensure we decode the content
            abortable_stream.stream.read = functools.partial(
                abortable_stream.stream.read,
                decode_content=True,
            )

            # Write the content to the destination file
            with open(dst, 'wb') as f:
                shutil.copyfileobj(abortable_stream, f)
        else:
            with open(dst, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)


class HttpDownloader(Downloader):
    """Downloader for HTTP and HTTPS URLs."""

    def download(self, src: str, dst: Path, *, abort: Event | None = None) -> Path:
        """Download a file from an HTTP or HTTPS URL."""
        logger.debug('starting http(s) download')
        session = self._create_session_with_retries()
        self._download(src, dst, session, abort=abort)
        return dst

    def _create_session_with_retries(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.1,  # type: ignore[arg-type]
            status_forcelist=[500, 502, 503, 504],
            allowed_methods={'GET'},
        )
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session


class GoogleSheetsDownloader(Downloader):
    """Downloader for Google Sheets URLs."""

    def download(self, src: str, dst: Path, *, abort: Event | None = None) -> Path:
        """Download a Google Sheet."""
        logger.debug('starting Google Sheets download')
        session = google_helper().get_session()
        self._download(src, dst, session, abort=abort)
        return dst


class GoogleStorageDownloader(Downloader):
    """Downloader for Google Storage URLs."""

    def download(self, src: str, dst: Path, *, abort: Event | None = None) -> Path:
        """Download a file from Google Storage."""
        logger.debug('starting google storage download')
        google_helper().download_to_file(src, dst)
        return dst


class DownloadHelper:
    """Helper that downloads files from various sources."""

    def __init__(self):
        self.strategies = {
            'google_sheets': GoogleSheetsDownloader(),
            'http': HttpDownloader(),
            'https': HttpDownloader(),
            'gs': GoogleStorageDownloader(),
        }

    def download(self, src: str, dst: Path | str, abort: Event | None = None) -> Path:
        """Download a file."""
        dst = self._prepare_destination(dst)
        protocol = self._get_protocol(src)

        if protocol not in self.strategies:
            raise HelperError(f'unknown protocol {protocol}')

        return self.strategies[protocol].download(src, dst, abort=abort)

    def _prepare_destination(self, dst: Path | str) -> Path:
        logger.debug(f'preparing to download to {dst!r}')
        if isinstance(dst, str):
            dst = Path(dst)
        dst = absolute_path(dst)
        check_fs(dst)
        return dst

    def _get_protocol(self, src: str) -> str:
        if src.startswith('https://docs.google.com/spreadsheets/d'):
            return 'google_sheets'
        return src.split(':')[0]


def download(src: str, dst: Path | str, *, abort: Event | None = None) -> Path:
    """Instantiate a DownloadHelper and download a file."""
    return DownloadHelper().download(src, dst, abort=abort)

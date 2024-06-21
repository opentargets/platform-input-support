import functools
import shutil
from pathlib import Path
from threading import Event

import requests
import requests.adapters
from loguru import logger
from urllib3 import Retry

from platform_input_support.helpers import google_helper
from platform_input_support.util.errors import DownloadError, TaskAbortedError
from platform_input_support.util.fs import check_dir, get_full_path

# we are going to download big files, better to use a big chunk size
CHUNK_SIZE = 1024 * 1024 * 10


class AbortableStreamWrapper:
    def __init__(self, stream, abort):
        self.stream = stream
        self.abort = abort

    def read(self, *args, **kwargs):
        if self.abort and self.abort.is_set():
            raise TaskAbortedError
        return self.stream.read(*args, **kwargs)


def download(src: str, dst: Path | str, *, abort: Event | None = None) -> Path:
    if isinstance(dst, str):
        dst = Path(src)
    dst = get_full_path(dst)
    logger.info(f'preparing to download `{src}` to `{dst}`')
    check_dir(dst)

    # download from google sheets
    if src.startswith('https://docs.google.com/spreadsheets/d'):
        logger.info('starting google sheets download')
        s = google_helper.get_session()
        _download(src, dst, s, abort)

    else:
        proto = src.split(':')[0]

        # download from http/https
        if proto in ['http', 'https']:
            logger.info('starting http(s) download')

            s = requests.Session()
            retries = Retry(
                total=5,
                backoff_factor=0.1,  # type: ignore[arg-type]
                status_forcelist=[500, 502, 503, 504],
                allowed_methods={'GET'},
            )

            s.mount('http://', requests.adapters.HTTPAdapter(max_retries=retries))
            s.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))
            _download(src, dst, s, abort)

        # download from google storage
        elif proto == 'gs':
            logger.info('starting google storage download')
            google_helper.download(src, dst)

        # unknown protocol
        else:
            raise ValueError(f'unknown protocol `{proto}`')

    return dst


def _download(src: str, dst: Path, s: requests.Session, abort: Event | None = None):
    r = s.get(src, stream=True, timeout=(10, None))
    r.raise_for_status()

    # Wrap r.raw with an AbortableStreamWrapper
    abortable_stream = AbortableStreamWrapper(r.raw, abort)
    # Ensure we decode the content
    abortable_stream.stream.read = functools.partial(
        abortable_stream.stream.read,
        decode_content=True,
    )

    # Write the content to the destination file
    with open(dst, 'wb') as f:
        try:
            shutil.copyfileobj(abortable_stream, f)
        except Exception as e:
            raise DownloadError(src, e)

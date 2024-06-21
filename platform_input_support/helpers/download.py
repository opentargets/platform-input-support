import functools
import shutil
from pathlib import Path

import requests
import requests.adapters
from loguru import logger
from urllib3 import Retry

from platform_input_support.helpers import google_helper
from platform_input_support.util.errors import DownloadError
from platform_input_support.util.fs import check_dir, get_full_path

# we are going to download big files, better to use a big chunk size
CHUNK_SIZE = 1024 * 1024 * 10


def download(src: str, dst: Path) -> Path:
    dst = get_full_path(dst)
    logger.info(f'preparing to download `{src}` to `{dst}`')
    check_dir(dst)

    # download from google sheets
    if src.startswith('https://docs.google.com/spreadsheets/d'):
        logger.info('starting google sheets download')
        s = google_helper.get_session()
        _download(src, dst, s)

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
            _download(src, dst, s)

        # download from google storage
        elif proto == 'gs':
            logger.info('starting google storage download')
            google_helper.download(src, dst)

    return dst


def _download(src: str, dst: Path, s: requests.Session):
    r = s.get(src, stream=True, timeout=(10, None))
    r.raise_for_status()

    # ensure we decode the content
    r.raw.read = functools.partial(r.raw.read, decode_content=True)

    with open(dst, 'wb') as f:
        try:
            shutil.copyfileobj(r.raw, f)
        except Exception as e:
            raise DownloadError(src, e)

import shutil
from pathlib import Path

import requests
import requests.adapters
from loguru import logger
from urllib3 import Retry

from platform_input_support.config import config
from platform_input_support.helpers.google import google

CHUNK_SIZE = 8192


class DownloadError(Exception):
    pass


def _ensure_path_exists(path: Path):
    parent = path.parent

    try:
        logger.info(f'ensuring path {parent} exists')
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f'error creating path {parent}: {e}')
        raise


def download(source: str, destination: str):
    complete_destination_path = Path(config.output_path) / destination

    try:
        _ensure_path_exists(complete_destination_path)
    except OSError as e:
        raise DownloadError(f'error creating path {complete_destination_path}: {e}')

    if source.startswith('https://docs.google.com/spreadsheets/d'):
        download_spreadsheet(source, complete_destination_path)
    else:
        protocol = source.split(':')[0]
        if protocol in ['http', 'https']:
            download_http(source, complete_destination_path)
        elif protocol == 'gs':
            google.download(source, complete_destination_path)

    logger.info(f'downloaded {source} to {destination}')


def download_http(source: str, destination: Path):
    s = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods={'GET'},
    )

    s.mount('http://', requests.adapters.HTTPAdapter(max_retries=retries))
    s.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))
    _download(source, destination, s)


def download_spreadsheet(source: str, destination: Path):
    s = google.get_session()
    _download(source, destination, s)


def _download(source: str, destination: Path, s: requests.Session, stream: bool = False):
    r = s.get(source, stream=True)
    r.raise_for_status()

    with open(destination, 'wb') as f:
        shutil.copyfileobj(r.raw, f, CHUNK_SIZE)

    logger.debug(f'downloaded {source} to {destination}')

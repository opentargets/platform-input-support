from pathlib import Path
from venv import logger

import requests
import requests.adapters
from urllib3 import Retry

from platform_input_support.config import config
from platform_input_support.helpers.google import google

CHUNK_SIZE = 8192


class DownloadError(Exception):
    pass


def _ensure_path_exists(path: Path):
    try:
        logger.info(f'ensuring path {path} exists')
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f'error creating path {path}: {e}')
        raise


def download(source: str, destination: str):
    complete_destination_path = Path(config.output_path) / destination

    try:
        _ensure_path_exists(complete_destination_path)
    except OSError as e:
        raise DownloadError(f'error creating path {complete_destination_path}: {e}')

    protocol = source.split(':')[0]
    if protocol in ['http', 'https']:
        download_http(source, complete_destination_path)
    elif protocol == 'gs':
        google.download(source, complete_destination_path)


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

    response = s.get(source, stream=True)
    if response.status_code == 200:
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
    else:
        raise DownloadError(f'response status code: {response.status_code}')

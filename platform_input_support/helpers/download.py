import shutil
from pathlib import Path

import requests
import requests.adapters
from loguru import logger
from urllib3 import Retry

from platform_input_support.config import config
from platform_input_support.helpers.google import google

__all__ = ['DownloadError', 'DownloadHelper']
CHUNK_SIZE = 1024 * 1024 * 10


class DownloadError(Exception):
    pass


class DownloadHelper:
    def __init__(self, source: str, destination: str):
        self.source = source
        self.destination = Path(config.output_path) / destination

    def _ensure_path_exists(self):
        parent = self.destination.parent

        try:
            logger.info(f'ensuring path {parent} exists')
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise DownloadError(f'error creating path {self.destination}: {e}')

    def download(self) -> str:
        logger.info(f'downloading {self.source} to {self.destination}')

        self._ensure_path_exists()

        if self.source.startswith('https://docs.google.com/spreadsheets/d'):
            self.download_spreadsheet()
        else:
            protocol = self.source.split(':')[0]
            if protocol in ['http', 'https']:
                self.download_http()
            elif protocol == 'gs':
                google.download(self.source, self.destination)

        logger.info('download successful')
        return f'downloaded {self.source} to {self.destination}'

    def download_http(self):
        s = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods={'GET'},
        )

        s.mount('http://', requests.adapters.HTTPAdapter(max_retries=retries))
        s.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))
        self._download(s, True)

    def download_spreadsheet(self):
        s = google.get_session()
        self._download(s)

    def _download(self, s: requests.Session, stream: bool = False):
        r = s.get(self.source, stream=True)
        r.raise_for_status()

        with open(self.destination, 'wb') as f:
            shutil.copyfileobj(r.raw, f, CHUNK_SIZE)

import shutil
from pathlib import Path
from typing import Any

import requests
import requests.adapters
from loguru import logger
from urllib3 import Retry

from platform_input_support.config import config
from platform_input_support.helpers import google

__all__ = ['DownloadError', 'DownloadHelper']
CHUNK_SIZE = 1024 * 1024 * 10


class DownloadError(Exception):
    pass


class DownloadHelper:
    def __init__(self, source: str, destination: str | None = None):
        self.source = source
        if destination:
            self.destination = Path(config.output_path) / destination

    def _ensure_path_exists(self):
        parent = self.destination.parent

        try:
            logger.info(f'ensuring path {parent} exists')
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise DownloadError(f'error creating path {self.destination}: {e}')

    def download(self) -> str:
        if not self.destination:
            raise DownloadError('destination not set')

        logger.info(f'downloading {self.source} to {self.destination}')

        self._ensure_path_exists()

        if self.source.startswith('https://docs.google.com/spreadsheets/d'):
            self._download_spreadsheet()
        else:
            protocol = self.source.split(':')[0]
            if protocol in ['http', 'https']:
                r = self._download_http()
                self._save_response(r)
            elif protocol == 'gs':
                google.download(self.source, self.destination)

        logger.info('download successful')
        return f'downloaded {self.source} to {self.destination}'

    def download_json(self) -> Any:
        logger.info(f'downloading json from {self.source}')

        try:
            r = self._download_http()
        except requests.RequestException as e:
            raise DownloadError(f'error downloading {self.source}: {e}')

        try:
            json = r.json()
        except requests.JSONDecodeError as e:
            raise DownloadError(f'error decoding json: {e}')

        logger.info('download successful')
        return json

    def _download_http(self) -> requests.Response:
        s = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.1,  # type: ignore[arg-type]
            status_forcelist=[500, 502, 503, 504],
            allowed_methods={'GET'},
        )

        s.mount('http://', requests.adapters.HTTPAdapter(max_retries=retries))
        s.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))
        return self._download(s)

    def _download_spreadsheet(self):
        s = google.get_session()
        self._download(s)

    def _download(self, s: requests.Session) -> requests.Response:
        r = s.get(self.source, stream=True, timeout=(10, None))
        r.raise_for_status()
        return r

    def _save_response(self, r: requests.Response):
        with open(self.destination, 'wb') as f:
            shutil.copyfileobj(r.raw, f, CHUNK_SIZE)

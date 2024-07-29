from pathlib import Path

import requests
from loguru import logger

from platform_input_support.util.fs import get_full_path

REQUEST_TIMEOUT = 10


def file_exists(path: Path) -> bool:
    logger.trace(path)
    return get_full_path(path).exists()


def file_size(source: str, destination: Path) -> bool:
    logger.debug(f'checking if {source} and {destination} are the same size')

    # this ensures no gzip encoding is used
    headers = {'accept-encoding': 'identity'}
    resp = requests.head(
        source,
        headers=headers,
        allow_redirects=True,
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    remote_size = 0
    if 'Content-Length' not in resp.headers:
        logger.warning('no content-length header in response, cannot validate file size')
        return True

    remote_size = int(resp.headers['Content-Length'])
    local_size = Path(get_full_path(destination)).stat().st_size

    logger.debug(f'checking if {remote_size} == {local_size}')
    return remote_size == local_size

from pathlib import Path

import requests
from loguru import logger

from platform_input_support.util.fs import absolute_path

REQUEST_TIMEOUT = 10


def file_exists(path: Path) -> bool:
    logger.trace(path)
    return absolute_path(path).exists()


def file_size(source: str, destination: Path) -> bool:
    logger.debug(f'checking if {source} and {destination} are the same size')

    # this ensures no gzip encoding is used
    headers = {'accept-encoding': 'identity'}

    try:
        resp = requests.head(
            source,
            headers=headers,
            allow_redirects=True,
            timeout=REQUEST_TIMEOUT,
        )
    except Exception as e:
        logger.warning(f'head request failed: {e}')
        return True

    if not resp.ok:
        logger.warning(f'head request returned {resp.status_code}, cannot validate file size')
        return True

    remote_size = 0
    if 'Content-Length' not in resp.headers:
        logger.warning('no content-length header in response, cannot validate file size')
        return True

    remote_size = int(resp.headers['Content-Length'])
    local_size = Path(absolute_path(destination)).stat().st_size

    logger.debug(f'checking if {remote_size} == {local_size}')
    return remote_size == local_size

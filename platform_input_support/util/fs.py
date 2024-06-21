import os
import sys
from pathlib import Path

from loguru import logger

from platform_input_support.config import settings


def check_dir(path: Path) -> None:
    parent = get_full_path(path).parent
    logger.debug(f'checking directory `{parent}`')

    if parent.is_dir():
        logger.debug('directory exists')
        if not os.access(parent, os.W_OK):
            logger.critical('directory is not writtable')
            sys.exit(1)
        logger.debug('directory is writtable')
    else:
        logger.info('directory does not exist, creating it')
        try:
            Path(parent).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.critical(f'error creating dir: {e}')
            sys.exit(1)

    if path.is_file():
        logger.info(f'file `{path}` already exists, deleting')
        try:
            path.unlink()
        except OSError as e:
            logger.critical(f'error deleting file: {e}')
    logger.success('directory checks passed')


def get_full_path(path: Path | str) -> Path:
    return (Path(settings.work_dir) / path).resolve()

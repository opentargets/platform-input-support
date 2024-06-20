import os
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from platform_input_support.config import settings

if TYPE_CHECKING:
    from platform_input_support.config.models import TaskDefinition
    from platform_input_support.task import Task


def check_dir(path: Path) -> None:
    parent = get_full_path(path).parent
    logger.debug(f'checking directory `{parent}`')

    if parent.is_dir():
        logger.debug('directory exists')
        if not os.access(parent, os.W_OK):
            logger.critical('directory is not writtable')
            sys.exit(1)
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


def get_full_path(path: Path | str) -> Path:
    return (Path(settings.work_dir) / path).resolve()


def date_str(d: datetime) -> str:
    return d.strftime('%Y-%m-%d %H:%M:%S')


def real_name(t: 'Task | TaskDefinition') -> str:
    if getattr(t, 'name', None):
        return t.name.split(' ')[0]
    elif isinstance(t, dict):
        name = t.get('name')
        if name:
            return name.split(' ')[0]
    raise ValueError(f'invalid task definition: {t}')

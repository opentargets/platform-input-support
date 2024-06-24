import os
import sys
from pathlib import Path

from loguru import logger

from platform_input_support.config import settings


def check_dir(path: Path) -> None:
    """Check working conditions for a path.

    The path can go all the way down to a file, or it can be a directory. The
    function will make sure that the directory exists, is writable, and that
    the file does not exist.

    Warning:
        The function will delete the file if it already exists.

    Args:
        path (Path): The path to the file or directory.

    Raises:
        SystemExit: If the directory is not writable.
        SystemExit: If there is an error creating the directory.
        SystemExit: If there is an error deleting the file.

    Returns:
        None: If all checks pass.
    """
    parent = get_full_path(path).parent
    logger.debug(f'checking directory {parent}')

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
        logger.info(f'file {path} already exists, deleting')
        try:
            path.unlink()
        except OSError as e:
            logger.critical(f'error deleting file: {e}')
            sys.exit(1)
    logger.info('directory checks passed')


def get_full_path(path: Path | str) -> Path:
    """Get the full path of a file or directory.

    Args:
        path (Path | str): The path to the file or directory.

    Returns:
        str: The full path of the file or directory.
    """
    return (Path(settings().work_dir) / path).resolve()

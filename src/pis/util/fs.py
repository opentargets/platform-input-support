"""File system utilities."""

import os
import sys
from pathlib import Path

from loguru import logger

from pis.config import settings


def check_file(path: Path) -> None:
    """Check working conditions for a file.

    The function will make sure that a file does not exist in the given path.

    .. warning:: The function will delete the file if it already exists.

    :param path: The path to check. Must be a file.
    :type path: Path
    :raises SystemExit: If there is an error deleting the file.
    :return: `None` if all checks pass.
    :rtype: None
    """
    path = absolute_path(path)
    logger.debug(f'checking file {path}')

    if path.is_file():
        logger.warning(f'file {path} already exists, deleting')
        try:
            path.unlink()
        except OSError as e:
            logger.critical(f'error deleting file: {e}')
            sys.exit(1)
    logger.debug('file checks passed')


def check_dir(path: Path) -> None:
    """Check working conditions for a path.

    The function will make sure that the directory exists and is writable. If it
    does not exist, the function will attempt to create it.

    :param path: The path to check. Must be a directory.
    :type path: Path
    :raises SystemExit: If the directory is not writable.
    :raises SystemExit: If there is an error creating the directory.
    :return: `None` if all checks pass.
    :rtype: None
    """
    if path.is_file():
        logger.critical('path exists and is a file, expected a directory')
        sys.exit(1)

    path = absolute_path(path)
    logger.debug(f'checking directory {path}')

    if path.is_dir():
        logger.debug('directory exists')
        if not os.access(path, os.W_OK):
            logger.critical('directory is not writtable')
            sys.exit(1)
        logger.debug('directory is writtable')
    else:
        logger.debug('directory does not exist, creating it')
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.critical(f'error creating dir: {e}')
            sys.exit(1)
    logger.debug('directory checks passed')


def check_fs(path: Path) -> None:
    """Check working conditions for a file and its parent directory.

    The function will make sure that the file does not exist and that the parent
    directory exists and is writable. If the parent directory does not exist, the
    function will attempt to create it.

    .. warning:: The function will delete the file if it already exists.

    :param path: The path to check. Must be a file.
    :type path: Path
    :raises SystemExit: If the file already exists.
    :raises SystemExit: If the parent directory is not writable.
    :raises SystemExit: If there is an error creating the parent directory.
    :return: `None` if all checks pass.
    :rtype: None
    """
    check_dir(path.parent)
    check_file(path)
    logger.debug('file and directory checks passed')


def absolute_path(path: Path | str) -> Path:
    """Get the full path of a file or directory.

    The function will try to figure if the path contains the work directory. If
    not, it will be prepended.

    :param path: The path to the file or directory.
    :type path: Path | str
    :return: The full path of the file or directory.
    :rtype: Path
    """
    work_dir = Path(settings().work_dir)

    if isinstance(path, str):
        path = Path(path)

    if path.parts[: len(work_dir.parts)] == work_dir.parts:
        return path.resolve()
    else:
        return (work_dir / path).resolve()

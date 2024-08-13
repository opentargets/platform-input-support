import os
import sys
from pathlib import Path

from loguru import logger

from platform_input_support.config import settings


def check_file(path: Path) -> None:
    """Check working conditions for a file.

    The function will make sure that a file does not exist in the given path.

    Warning:
        The function will delete the file if it already exists.

    Args:
        path (Path): The path to check. Must be a file.

    Raises:
        SystemExit: If there is an error deleting the file.

    Returns:
        None: If all checks pass.
    """
    path = absolute_path(path)
    logger.debug(f'checking file {path}')

    if path.is_file():
        logger.info(f'file {path} already exists, deleting')
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

    Args:
        path (Path): The path to check. Must be a directory.

    Raises:
        SystemExit: If the directory is not writable.
        SystemExit: If there is an error creating the directory.

    Returns:
        None: If all checks pass.
    """
    if path.is_file():
        logger.critical('path exists and is a file, expected a directory')
        sys.exit(1)

    path = absolute_path(path)
    logger.debug(f'checking directory {path}')
    logger.debug(f'PATH: {path.is_dir()}')

    if path.is_dir():
        logger.debug('directory exists')
        if not os.access(path, os.W_OK):
            logger.critical('directory is not writtable')
            sys.exit(1)
        logger.debug('directory is writtable')
    else:
        logger.info('directory does not exist, creating it')
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

    Warning:
        The function will delete the file if it already exists.

    Args:
        path (Path): The path to check. Must be a file.

    Raises:
        SystemExit: If the file already exists.
        SystemExit: If the parent directory is not writable.
        SystemExit: If there is an error creating the parent directory.

    Returns:
        None: If all checks pass.
    """
    check_dir(path.parent)
    check_file(path)
    logger.info('file and directory checks passed')


def absolute_path(path: Path | str) -> Path:
    """Get the full path of a file or directory.

    The function will try to figure if the path contains the work directory. If
    not, it will be prepended.

    Args:
        path (Path | str): The path to the file or directory.

    Returns:
        str: The full path of the file or directory.
    """
    work_dir = Path(settings().work_dir)

    if isinstance(path, str):
        path = Path(path)

    if path.parts[: len(work_dir.parts)] == work_dir.parts:
        return path.resolve()
    else:
        return (work_dir / path).resolve()

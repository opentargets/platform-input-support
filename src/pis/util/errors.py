"""Custom exceptions for the pis package."""

import re
import sys
from pathlib import Path

from loguru import logger


class PISError(Exception):
    """Base class for all exceptions in the PIS package."""


class NotFoundError(PISError):
    """Raise when something is not found."""

    def __init__(self, msg: str | None = None):
        super().__init__(msg)


class PISCriticalError(PISError):
    """Raise when a critical error occurs."""

    def __init__(self, msg: str):
        logger.opt(exception=sys.exc_info()).critical(msg)
        super().__init__(msg)


class HelperError(PISError):
    """Raise when an error occurs in a helper."""

    def __init__(self, msg: str):
        super().__init__(msg)


class StorageError(PISError):
    """Raise when an error occurs in a storage class."""

    def __init__(self, msg: str):
        super().__init__(msg)


class DownloadError(PISError):
    """Raise when an error occurs during a download."""

    def __init__(self, src: str, error: Exception):
        msg = f'error downloading {src}: {error}'
        super().__init__(msg)


class TaskAbortedError(PISError):
    """Raise when a task is aborted."""

    def __init__(self):
        super().__init__('a previous task failed, task aborted')


class ScratchpadError(PISError):
    """Raise when a key is not found in the scratchpad."""

    def __init__(self, sentinel: str | Path):
        sentinel_label = re.sub(r'[^a-z.]', '', str(sentinel))
        msg = f'key {sentinel_label} not found in scratchpad'
        logger.opt(exception=sys.exc_info()).error(msg)
        super().__init__(msg)


class StepFailedError(PISError):
    """Raise when a step fails."""

    def __init__(self, step: str = '', func: str = ''):
        super().__init__(f'step {step} {func} failed')


class ValidationError(PISError):
    """Raise when a validation fails."""

    def __init__(self):
        super().__init__('validation failed')


class PreconditionFailedError(PISError):
    """Raise when a precondition fails."""

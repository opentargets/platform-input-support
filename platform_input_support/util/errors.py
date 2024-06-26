import re
import sys
from pathlib import Path

from loguru import logger


class PISError(Exception):
    pass


class NotFoundError(PISError):
    def __init__(self, resource: str):
        msg = f'{resource} not found'
        logger.opt(exception=sys.exc_info()).error(msg)
        super().__init__(msg)


class HelperError(PISError):
    def __init__(self, msg: str):
        logger.opt(exception=sys.exc_info()).error(msg)
        super().__init__(msg)


class DownloadError(PISError):
    def __init__(self, src: str, error: Exception):
        msg = f'error downloading {src}: {error}'
        super().__init__(msg)


class TaskAbortedError(PISError):
    def __init__(self):
        super().__init__('a previous task failed, task aborted')


class ScratchpadError(PISError):
    def __init__(self, sentinel: str | Path):
        sentinel_label = re.sub(r'[^a-z.]', '', str(sentinel))
        msg = f'key {sentinel_label} not found in scratchpad'
        logger.opt(exception=sys.exc_info()).error(msg)
        super().__init__(msg)


class StepFailedError(PISError):
    def __init__(self, step: str = '', func: str = ''):
        super().__init__(f'step {step} {func} failed')


class ValidationError(PISError):
    def __init__(self):
        super().__init__('validation failed')

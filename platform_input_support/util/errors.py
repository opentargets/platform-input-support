import sys

from loguru import logger


class NotFoundError(Exception):
    def __init__(self, resource: str):
        message = f'{resource} not found'
        logger.error(message)
        super().__init__(message)


class HelperError(Exception):
    def __init__(self, message: str):
        logger.error(message)
        super().__init__(message)


def log_and_raise(error: Exception) -> None:
    logger.opt(exception=sys.exc_info()).error(error)
    raise error

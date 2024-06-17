import sys

from loguru import logger


def log_and_raise(error: Exception) -> None:
    logger.opt(exception=sys.exc_info()).error(error)
    raise error

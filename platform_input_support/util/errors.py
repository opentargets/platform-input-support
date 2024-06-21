import sys

from loguru import logger


class PISError(Exception):
    pass


class NotFoundError(PISError):
    def __init__(self, resource: str):
        msg = f'`{resource}` not found'
        logger.opt(exception=sys.exc_info()).error(msg)
        super().__init__(msg)


class HelperError(PISError):
    def __init__(self, msg: str):
        logger.opt(exception=sys.exc_info()).error(msg)
        super().__init__(msg)


class DownloadError(PISError):
    def __init__(self, src: str, error: Exception):
        msg = f'error downloading `{src}`: {error}'
        logger.opt(exception=sys.exc_info()).error(msg)
        super().__init__(msg)

class ScratchpadError(PISError):
    def __init__(self, sentinel: str):
        msg = f'key `{sentinel}` not found in scratchpad'
        logger.opt(exception=sys.exc_info()).error(msg)
        super().__init__(msg)

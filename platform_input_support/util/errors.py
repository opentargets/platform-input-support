from loguru import logger


class PISError(Exception):
    pass


class NotFoundError(PISError):
    def __init__(self, resource: str):
        msg = f'`{resource}` not found'
        logger.error(msg)
        super().__init__(msg)


class HelperError(PISError):
    def __init__(self, msg: str):
        logger.error(msg)
        super().__init__(msg)


class DownloadError(PISError):
    def __init__(self, src: str, error: Exception):
        msg = f'error downloading `{src}`: {error}'
        logger.error(msg)
        super().__init__(msg)

from loguru import logger

from platform_input_support.util.errors import ValidationError


def v(func, *args, **kwargs) -> None:
    logger.debug(f'running validator {func.__name__}')

    result = func(*args, **kwargs)
    if result is False:
        raise ValidationError

    logger.debug(f'validator {func.__name__} passed')

import os
import sys

from loguru import logger
from pydantic import ValidationError

from platform_input_support.config.models import EnvSettings

ENV_PREFIX = 'PIS'


def to_setting(name: str) -> str:
    """Convert an environment variable name to a setting name."""
    return name[len(f'{ENV_PREFIX}_') :].lower()


def parse_env() -> EnvSettings:
    logger.debug('parsing environment variables')

    # this builds a dict of all environment variables that start with the prefix
    settings_dict = {to_setting(k): v for k, v in os.environ.items() if k.startswith(f'{ENV_PREFIX}_')}

    try:
        return EnvSettings.model_validate_strings(settings_dict)
    except ValidationError as e:
        logger.critical(f'error validating environment variables: {e}')
        sys.exit(1)

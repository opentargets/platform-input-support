"""This module contains the functions to parse the environment variables."""

import os
import sys

from loguru import logger
from pydantic import ValidationError

from pis.config.models import EnvSettings

ENV_PREFIX = 'PIS'


def to_setting(name: str) -> str:
    """Converts an environment variable name to a setting name.

    :param name: The environment variable name to convert.
    :type name: str
    :return: The setting name.
    :rtype: str
    """
    return name[len(f'{ENV_PREFIX}_') :].lower()


def parse_env() -> EnvSettings:
    """Parses the environment variables and returns an EnvSettings object.

    :return: The parsed environment variables.
    :rtype: EnvSettings
    """
    logger.debug('parsing environment variables')

    # this builds a dict of all environment variables that start with the prefix
    settings_dict = {to_setting(k): v for k, v in os.environ.items() if k.startswith(f'{ENV_PREFIX}_')}

    try:
        return EnvSettings.model_validate_strings(settings_dict)
    except ValidationError as e:
        logger.critical(f'error validating environment variables: {e}')
        sys.exit(1)

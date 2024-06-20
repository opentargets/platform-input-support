import os

from loguru import logger

from platform_input_support.config.models import EnvVarSettings

ENV_VAR_PREFIX = 'PIS'


def from_env_var(name: str) -> str:
    return name[len(f'{ENV_VAR_PREFIX}_') :].lower()


def parse_env() -> EnvVarSettings:
    logger.debug('parsing environment variables')

    settings_dict = {from_env_var(k): v for k, v in os.environ.items() if k.startswith(f'{ENV_VAR_PREFIX}_')}
    return EnvVarSettings.model_validate_strings(settings_dict)

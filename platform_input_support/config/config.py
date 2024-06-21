import sys

from loguru import logger

from platform_input_support.config.cli import parse_cli
from platform_input_support.config.env import parse_env
from platform_input_support.config.models import Settings
from platform_input_support.config.yaml import parse_yaml
from platform_input_support.util.misc import list_str


class Config:
    def __init__(self):
        settings = Settings()
        cli_settings = parse_cli()
        env_settings = parse_env()
        config_file = cli_settings.config_file or env_settings.config_file or settings.config_file
        yaml_settings, step_definitions, scratchpad = parse_yaml(config_file)

        # subsequently merge settings from different sources
        settings.merge_model(yaml_settings)
        settings.merge_model(env_settings)
        settings.merge_model(cli_settings)

        self.settings = settings
        self.step_definitions = step_definitions
        self.scratchpad = scratchpad

        settings_str = list_str(settings.model_dump(), dict_values=True)
        step_definitions_str = list_str(step_definitions)
        scratchpad_str = list_str(scratchpad.sentinel_dict, dict_values=True)
        logger.info(f'loaded settings: {settings_str}')
        logger.info(f'loaded {len(step_definitions)} step definitions: {step_definitions_str}')
        logger.info(f'loaded {len(scratchpad.sentinel_dict)} scratchpad values: {scratchpad_str}')

        # validate step setting
        if settings.step not in step_definitions:
            logger.critical(f'specified step `{settings.step}` not found in step definitions')
            sys.exit(1)

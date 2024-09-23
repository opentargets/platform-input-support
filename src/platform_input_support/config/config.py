"""Main module in the config package."""

from typing import Any

from loguru import logger
from pydantic import ValidationError

from platform_input_support.config.cli import parse_cli
from platform_input_support.config.env import parse_env
from platform_input_support.config.models import BaseTaskDefinition, Settings
from platform_input_support.config.yaml import get_yaml_settings, parse_yaml
from platform_input_support.util.misc import list_str


class Config:
    """The configuration object.

    This class loads the settings from different sources and merges them into a
    single settings object. The sources are, in order of precedence:

    1. Command line arguments
    2. Environment variables
    3. YAML configuration file
    4. Default settings

    :ivar Settings settings: The settings object.
    """

    def __init__(self):
        # load settings from different sources
        settings = Settings()
        cli_settings = parse_cli()
        env_settings = parse_env()
        config_file = cli_settings.config_file or env_settings.config_file or settings.config_file
        self.yaml_dict = parse_yaml(config_file)
        yaml_settings = get_yaml_settings(self.yaml_dict)

        # subsequently merge settings from different sources
        settings.merge_model(yaml_settings)
        settings.merge_model(env_settings)
        settings.merge_model(cli_settings)

        self.settings = settings
        logger.info(f'loaded settings: {list_str(self.settings.model_dump(), dict_values=True)}')

    def _validate_step(self):
        """Validate the step.

        Makes sure the step specified in the CLI arguments is defined in the
        configuration file.
        """
        if not self.settings.step:
            logger.critical('empty step argument, please provide a step')
            raise SystemExit(1)

        if self.settings.step not in self.yaml_dict['steps']:
            logger.critical(f'invalid step: {self.settings.step}')
            raise SystemExit(1)

    def get_task_definitions(self) -> list[BaseTaskDefinition]:
        """Validate the task definitions.

        Makes sure the task definitions specified in the configuration file for
        the step the application is going to run are valid.

        :return: The list of task definitions.
        :rtype: list[BaseTaskDefinition]
        """
        step = self.settings.step
        ts = self.yaml_dict['steps'].get(step)

        if not ts:
            logger.critical(f'no task definitions found for step: {step}')
            raise SystemExit(1)

        try:
            return [BaseTaskDefinition(**t) for t in ts]
        except ValidationError as e:
            logger.critical(f'invalid task definition for: {e}')
            raise SystemExit(1)

    def get_scratchpad_sentinel_dict(self) -> dict[str, Any]:
        """Return the sentinel dictionary for the scratchpad.

        :return: The sentinel dictionary for the scratchpad.
        :rtype: dict[str, Any]
        """
        return self.yaml_dict.get('scratchpad', {})

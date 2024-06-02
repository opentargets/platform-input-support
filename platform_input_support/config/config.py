import os
import sys
from pathlib import Path

# this module is initialized before the logger, so we must use loguru here
from loguru import logger

from platform_input_support.config.models import ConfigModel, SettingsModel
from platform_input_support.config.parse_cli import ParseCLI
from platform_input_support.config.parse_yaml import ParseYAML

__all__ = ['config']


class Config:
    def __init__(self):
        self.config: ConfigModel

        logger.debug('initializing configuration')

        # parse the cli arguments
        cli_parser = ParseCLI()
        cli_parser.parse()
        cli_settings = SettingsModel.from_dict(cli_parser.data)

        # parse the yaml file
        config_file_path = Path(cli_parser.data.get('config', 'config.yaml'))
        yaml_parser = ParseYAML(config_file_path)
        yaml_parser.parse()
        yaml_config = ConfigModel.from_dict(yaml_parser.data)

        # merge and validate settings
        merged_settings = yaml_config.settings + cli_settings
        self._check_output_path(merged_settings.output_path)

        # update config
        yaml_config.settings = merged_settings
        self.config = yaml_config

        # print info about the steps found in the config
        step_list = list(self.config.steps.keys())
        logger.debug('configuration initialization finished')
        logger.info(f'found {len(step_list)} steps: {step_list}')

    def _check_output_path(self, output_path: str) -> None:
        if Path(output_path).exists():
            logger.debug(f'output path exists: {output_path}')
            if not os.access(output_path, os.W_OK):
                logger.critical(f'output path is not writable: {output_path}')
                sys.exit(1)
        if not Path(output_path).is_dir():
            logger.info(f'output path does not exist, creating: {output_path}')

            try:
                Path(output_path).mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.critical(f'error creating output path: {e}')
                sys.exit(1)


c = Config()
config: ConfigModel = c.config

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

        logger.info('initializing configuration')

        # parse the cli arguments
        cli_parser = ParseCLI()
        cli_parser.parse()
        cli_settings = SettingsModel.from_dict(cli_parser.data)

        # parse the yaml file
        config_file_path = Path(cli_parser.data.get('config', 'config.yaml'))
        yaml_parser = ParseYAML(config_file_path)
        yaml_parser.parse()
        yaml_config = ConfigModel.from_dict(yaml_parser.data)

        # merge the config key from both parsers keeping the values from the cli parser
        yaml_config.settings += cli_settings

        # set the config attribute
        self.config = yaml_config

        # print info about the steps found in the config
        step_list = list(self.config.steps.keys())
        logger.info(f'found configuration for {len(step_list)} steps: {step_list}')


c = Config()
config: ConfigModel = c.config

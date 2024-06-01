from pathlib import Path

# this module is initialized before the logger, so we must use loguru here
from loguru import logger

from platform_input_support.config.parse_cli import ParseCLI
from platform_input_support.config.parse_yaml import ParseYAML

__all__ = ['config']


class Config:
    def __init__(self):
        self.config: dict = {}

        logger.info('initializing configuration')

        cli_parser = ParseCLI()
        cli_parser.parse()

        config_file_path = Path(cli_parser.data.get('config', 'config.yaml'))
        del cli_parser.data['config']

        yaml_parser = ParseYAML(config_file_path)
        yaml_parser.parse()

        # merge the config key from both parsers keeping the values from the cli parser
        self.config = {**yaml_parser.data, 'config': {**yaml_parser.data['config'], **cli_parser.data}}

        steps = self.config['steps']
        step_names = ', '.join(list(steps.keys()))
        logger.info(f'{len(steps)} steps parsed from config: {step_names}')


c = Config()
config = c.config

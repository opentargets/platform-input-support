import os
import sys
from pathlib import Path

# this module is initialized before the logger, so we must use loguru here
from loguru import logger

from platform_input_support.config.models import ConfigMapping, RootMapping, StepMapping
from platform_input_support.config.parse_cli import ParseCLI
from platform_input_support.config.parse_yaml import ParseYAML

__all__ = ['config']


class Config:
    def __init__(self):
        self.config: RootMapping

        logger.debug('initializing configuration')

        # parse the cli arguments
        cli_parser = ParseCLI()
        cli_parser.parse()
        cli_config = ConfigMapping.from_dict(cli_parser.data)

        # parse the yaml file
        config_file_path = Path(cli_parser.data.get('config', 'config.yaml'))
        yaml_parser = ParseYAML(config_file_path)
        yaml_parser.parse()
        yaml_root = RootMapping.from_dict(yaml_parser.data)

        # merge and validate settings
        merged_config = yaml_root.config + cli_config
        self._check_output_path(merged_config.output_path)

        # update config
        yaml_root.config = merged_config
        self.config = yaml_root

        # print info about the steps found in the config
        step_list = list(self.config.steps.keys())
        logger.debug('configuration initialization finished')
        logger.info(f'found {len(step_list)} steps: {step_list}')

    def _check_output_path(self, output_path: str) -> None:
        if Path(output_path).exists():
            logger.debug(f'output path {output_path} exists')
            if not os.access(output_path, os.W_OK):
                logger.critical(f'output path {output_path} is not writable')
                sys.exit(1)
        if not Path(output_path).is_dir():
            logger.info(f'output path {output_path} does not exist, creating it')

            try:
                Path(output_path).mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.critical(f'error creating output path: {e}')
                sys.exit(1)


c = Config()
config: ConfigMapping = c.config.config
steps: dict[str, StepMapping] = c.config.steps
scratch_pad: dict[str, str] = c.config.scratch_pad

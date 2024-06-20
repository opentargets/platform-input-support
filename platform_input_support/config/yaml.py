import sys
from pathlib import Path

import yaml
from loguru import logger

from platform_input_support.config.models import TaskDefinition, YamlSettings
from platform_input_support.config.scratchpad import Scratchpad


def parse_yaml(config_file: Path) -> tuple[YamlSettings, dict[str, list[TaskDefinition]], Scratchpad]:
    logger.debug(f'parsing yaml file `{config_file}`')

    try:
        yaml_str = Path.read_text(config_file)
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.critical(f'error reading config file: {e}')
        sys.exit(1)

    try:
        yaml_dict = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        logger.critical(f'error parsing config file: {e}')
        sys.exit(1)

    step_definitions_dict = yaml_dict.pop('steps', {})
    scratchpad_dict = yaml_dict.pop('scratchpad', {})
    settings_dict = {k: v for k, v in yaml_dict.items() if v is not None}

    settings = YamlSettings.model_validate(settings_dict)
    scratchpad = Scratchpad.model_validate({'sentinel_dict': scratchpad_dict})
    step_definitions = {k: [TaskDefinition.model_validate(t) for t in v] for k, v in step_definitions_dict.items()}

    return settings, step_definitions, scratchpad

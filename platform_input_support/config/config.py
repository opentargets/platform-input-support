from platform_input_support.config.cli import parse_cli
from platform_input_support.config.env import parse_env
from platform_input_support.config.models import Settings
from platform_input_support.config.yaml import parse_yaml


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

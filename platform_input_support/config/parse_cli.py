import argparse
import os

from loguru import logger

from .models import ConfigMapping


class WithEnvironmentVariable(argparse.Action):
    def __init__(self, required=False, default=None, **kwargs):
        option_string: list[str] = kwargs.get('option_strings', [])
        env_var_name = 'PIS_' + option_string[-1][2:].upper().replace('-', '_')
        default = os.environ.get(env_var_name, default)
        if default is not None:
            default = default.lower()
        kwargs['help'] += f' (environment variable: {env_var_name})'
        if required and default:
            required = False

        super().__init__(default=default, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


class WithDefaultsFromDataclassHelpFormatter(argparse.HelpFormatter):
    def _get_help_string(self, action):
        example_data = ConfigMapping('dummy')
        help_ = action.help
        required = action.required
        default = example_data.__dict__.get(action.dest)
        if not required and help_ is not None and default is not None and action.default is not argparse.SUPPRESS:
            defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
            if action.option_strings or action.nargs in defaulting_nargs:
                help_ += f' (default: {default})'
        return help_


class ParseCLI:
    def __init__(self) -> None:
        self.data = {}

    def parse(self):
        logger.debug('parsing cli arguments')

        parser = argparse.ArgumentParser(
            description='Open Targets platform input support application.',
            formatter_class=WithDefaultsFromDataclassHelpFormatter,
        )

        parser.add_argument(
            '-s',
            '--step',
            action=WithEnvironmentVariable,
            required=True,
            help='The step to run',
        )

        parser.add_argument(
            '-c',
            '--config',
            default='./config.yaml',
            action=WithEnvironmentVariable,
            help='The path for the configuration file.',
        )

        parser.add_argument(
            '-o',
            '--output-path',
            # default is './output', set in the SettingsModel
            action=WithEnvironmentVariable,
            help='The path for the output directory.',
        )

        parser.add_argument(
            '-b',
            '--gcs-url',
            action=WithEnvironmentVariable,
            help='If set, platform-input-support will use this google cloud storage '
            'url to retrieve the manifest status, and act accordingly to what is there. '
            'Also, the resulting files will be uploaded there.',
        )

        parser.add_argument(
            '-l',
            '--log-level',
            # default is 'INFO', set in the SettingsModel
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            action=WithEnvironmentVariable,
            help='Log level for the application.',
        )

        self.data = vars(parser.parse_args())

import argparse
import os

from loguru import logger

from platform_input_support.config.models import ConfigMapping


class WithEnvironmentVariable(argparse.Action):
    def __init__(self, required=False, default=None, **kwargs):
        option_string: list[str] = kwargs.get('option_strings', [])

        env_var_name = 'PIS_' + option_string[-1][2:].upper().replace('-', '_')
        default = os.environ.get(env_var_name, default)
        kwargs['help'] += f' (environment variable: {env_var_name})'
        if required and default:
            required = False

        super().__init__(default=default, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


class StoreLowercaseSetAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values is not None:
            unique_values = {value.lower() for value in values}
            setattr(namespace, self.dest, unique_values)


class WithDefaultsFromDataclassHelpFormatter(argparse.HelpFormatter):
    def _get_help_string(self, action):
        example_data = ConfigMapping()
        help_ = action.help
        default = example_data.__dict__.get(action.dest)
        if help_ is not None and default is not None and action.default is not argparse.SUPPRESS:
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
            '-g',
            '--gcp-credentials-path',
            action=WithEnvironmentVariable,
            help='The path were the JSON credential file is stored.',
        )

        parser.add_argument(
            '-b',
            '--gcp-bucket-path',
            action=WithEnvironmentVariable,
            help='If set, the result will be uploaded to this google cloud storage path.',
        )

        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '-i',
            '--include',
            nargs='+',
            action=StoreLowercaseSetAction,
            help='Run a given step or list of steps. Cannot be specified in an environment '
            'variable. This argument is mutually exclusive with --exclude.',
        )
        group.add_argument(
            '-e',
            '--exclude',
            nargs='+',
            action=StoreLowercaseSetAction,
            help='Run all steps except for the given step or list of steps. Cannot be specified in '
            'an environment variable. This argument is mutually exclusive with --steps.',
        )

        parser.add_argument(
            '--log-level',
            # default is 'INFO', set in the SettingsModel
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            action=WithEnvironmentVariable,
            help='Log level for the application.',
        )

        self.data = vars(parser.parse_args())

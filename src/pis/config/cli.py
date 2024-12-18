"""This module contains the functions to parse the command line arguments."""

import argparse
import os

from loguru import logger

from pis.config.env import ENV_PREFIX
from pis.config.models import CliSettings, Settings


def to_env(var: str) -> str:
    """Converts a variable name to an environment variable name.

    :param var: The variable name to convert.
    :type var: str
    :return: The environment variable name.
    :rtype: str
    """
    return f'{ENV_PREFIX}_{var.upper()}'


def parse_cli() -> CliSettings:
    """Parses the command line arguments and returns a CliSettings object.

    :return: The parsed command line arguments.
    :rtype: CliSettings
    """
    logger.debug('parsing cli arguments')

    class HelpFormatter(argparse.HelpFormatter):
        def _get_help_string(self, action):
            if action.default is not argparse.SUPPRESS:
                action.help = f'{action.help} (environment variable: {to_env(action.dest)})'
                default_value = Settings.model_fields[action.dest].default
                if default_value != '':  # noqa: PLC1901
                    action.help += f' (default: {default_value})'
            return f'{action.help}'

    parser = argparse.ArgumentParser(
        description='Open Targets Pipeline Input Stage application.',
        formatter_class=HelpFormatter,
    )

    parser.add_argument(
        '-s',
        '--step',
        required=to_env('step') not in os.environ,
        help='The step to run',
    )

    parser.add_argument(
        '-c',
        '--config-file',
        help='The path for the configuration file.',
    )

    parser.add_argument(
        '-w',
        '--work-dir',
        help='The local working path. This is where files will be downloaded and '
        'the manifest and logs will be written to.',
    )

    parser.add_argument(
        '-r',
        '--remote-uri',
        help='If set, this URI will be used as remote working path. This is where '
        'files will be uploaded and the manifest and logs will be written to.'
        'If omitted, the run will be local only.',
    )

    parser.add_argument(
        '-p',
        '--pool',
        type=int,
        help='The number of worker proccesses that will be spawned to run tasks'
        'in the step in parallel. It should be similar to the number of cores,'
        'but could be higher because there is a lot of I/O blocking.',
    )

    parser.add_argument(
        '-l',
        '--log-level',
        choices=['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Log level for the application.',
    )

    settings_vars = vars(parser.parse_args())
    settings_dict = {k: v for k, v in settings_vars.items() if v is not None}

    return CliSettings.model_validate(settings_dict)

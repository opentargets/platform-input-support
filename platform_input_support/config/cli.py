import argparse
import os

from loguru import logger

from platform_input_support.config.env import ENV_PREFIX
from platform_input_support.config.models import CliSettings, Settings


def to_env(var: str) -> str:
    """Convert a setting name to an environment variable name."""
    return f'{ENV_PREFIX}_{var.upper()}'


def parse_cli() -> CliSettings:
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
        description='Open Targets platform input support application.',
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
        help='The local working directory path, this is where files will be '
        'downloaded and the manifest and logs will be written to before upload '
        'to the GCS bucket.',
    )

    parser.add_argument(
        '-b',
        '--gcs-url',
        help='If set, platform-input-support will use this google cloud storage '
        'url to retrieve the manifest status, and act accordingly to what is '
        'there. Also, the resulting files will be uploaded there.',
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

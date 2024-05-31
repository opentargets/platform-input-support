import argparse
import os

from loguru import logger


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


class ParseCLI:
    def __init__(self) -> None:
        self.data = {}

    def parse(self):
        logger.debug('parsing cli arguments')

        parser = argparse.ArgumentParser(
            description='Open Targets platform input support application.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
            default='./output',
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
            '-s',
            '--steps',
            default=[],
            nargs='+',
            help='Run only a given step or list of steps. Cannot be specified in an environment '
            'variable. This argument is mutually exclusive with --exclude.',
        )
        group.add_argument(
            '-e',
            '--exclude',
            default=[],
            nargs='+',
            help='Run all steps except for the given step or list of steps. Cannot be specified in '
            'an environment variable. This argument is mutually exclusive with --steps.',
        )

        parser.add_argument(
            '--log-level',
            default='INFO',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            action=WithEnvironmentVariable,
            help='Log level for the application.',
        )

        parser.add_argument(
            '--log-filename',
            default=os.environ.get('PIS_LOG_FILE', 'platform_input_support.log'),
            action=WithEnvironmentVariable,
            help='Log file name. The application will only log to standard output by default, but '
            'if this argument is present, the log will be written to the file as well.',
        )

        self.data = vars(parser.parse_args())

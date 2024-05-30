import configargparse


def setup_parser():
    """Define the input parameters and defines some default values."""
    p = configargparse.get_argument_parser(config_file_parser_class=configargparse.YAMLConfigFileParser)
    p.description = 'Open Targets platform input support'

    # argument to read config file
    p.add(
        '-c',
        '--config',
        is_config_file=True,
        env_var='PIS_CONFIG',
        help='The path to the configuration file.',
    )

    p.add(
        '-gkey',
        '--gcp_credentials',
        env_var='GCP_CREDENTIALS',
        help='The path were the JSON credential file is stored.',
    )

    p.add(
        '-gb',
        '--gcp_bucket',
        env_var='GCP_BUCKET',
        help='Google storage bucket where files will be copied from the output directory.',
    )

    p.add(
        '-o',
        '--output_dir',
        env_var='OT_OUTPUT_DIR',
        help='Output directory. By default, the files are generated in the root directory.',
    )

    p.add(
        '-f',
        '--force-clean',
        action='store_false',
        default=True,
        env_var='OT_CLEAN_OUTPUT',
        help='By default, the output directory is deleted. To not delete the files use this flag.',
    )

    p.add(
        '-s',
        '--suffix',
        env_var='OT_SUFFIX_INPUT',
        action='store',
        help='The default suffix is yyyy-mm-dd.',
    )

    p.add(
        '-steps',
        action='store',
        nargs='+',
        default=[],
        help='Run a specific list of sections of the config file. Eg\n annotations annotations_from_buckets',
    )

    p.add(
        '-exclude',
        action='store',
        nargs='+',
        default=[],
        help='Exclude a specific list of sections of the config file. Eg\n annotations annotations_from_buckets',
    )

    # logging
    p.add(
        '--log-level',
        help='set the log level',
        env_var='LOG_LEVEL',
        action='store',
        default='INFO',
    )

    return p


def get_args():
    """Get the list of args passed by the command line."""
    return configargparse.get_argument_parser().parse_known_args()[0]

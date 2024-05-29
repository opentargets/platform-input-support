import os
import logging
import configargparse
from platform_input_support import ROOT_DIR
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_parser():
    """
    This function defines the input parameters and defines some default values.
    """
    p = configargparse.get_argument_parser(config_file_parser_class=configargparse.YAMLConfigFileParser)
    p.description = 'Open Targets platform input support'

    # argument to read config file
    p.add('-c', '--config', is_config_file=True,
          env_var="PIS_CONFIG", help='path to config file (YAML)')

    p.add('-gkey', '--gcp_credentials',
          env_var="GCP_CREDENTIALS", help='The path were the JSON credential file is stored.')

    p.add('-gb', '--gcp_bucket',
          env_var="GCP_BUCKET", help='Copy the files from the output directory to a specific google bucket')

    p.add('-o', '--output_dir',
          env_var="OT_OUTPUT_DIR", help='By default, the files are generated in the root directory')

    p.add('-f', '--force-clean', action='store_false', default=True,
          env_var="OT_CLEAN_OUTPUT",
          help='By default, the output directory is deleted. To not delete the files use this flag.')

    p.add('-s', '--suffix', env_var="OT_SUFFIX_INPUT",
          action='store', help='The default suffix is yyyy-mm-dd')

    p.add('-steps', action='store', nargs='+', default=[],
          help='Run a specific list of sections of the config file. Eg\n annotations annotations_from_buckets'
          )

    p.add('-exclude', action='store', nargs='+', default=[],
          help='Exclude a specific list of sections of the config file. Eg\n annotations annotations_from_buckets'
          )

    # logging
    p.add("--log-level", help="set the log level",
          env_var="LOG_LEVEL", action='store', default='INFO')
    p.add("--log-config", help="logging configuration file",
          env_var="LOG_CONFIG", action='store', default='resources/logging.ini')

    return p


def get_args():
    """
    Get the list of args passed by the command line
    """
    return configargparse.get_argument_parser().parse_known_args()[0]


def setBasicConfigLog():
    """
    Set Logging subsystem baseline configuration
    """
    logfilename = Path(ROOT_DIR) / 'log/output.log'
    logging.basicConfig(level=logging.INFO, filename=logfilename, format='%(name)-12s: %(levelname)-8s %(message)s',
                        datefmt='%H:%M:%S')

    # set up logging to console
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    return logging.getLogger(__name__)


def set_up_logging(args):
    """
    Setup logging configuration according to command line arguments
    """
    # set up logging
    if args.log_config:
        if os.path.isfile(args.log_config) and os.access(args.log_config, os.R_OK):
            logging.config.fileConfig(Path(ROOT_DIR) / args.log_config, disable_existing_loggers=False)
            logger = logging.getLogger(__name__ + ".main()")
        else:
            logger = setBasicConfigLog()
            logger.warning("unable to read file {}".format(args.log_config))
    else:
        logger = setBasicConfigLog()
    if args.log_level:
        try:
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.getLevelName(args.log_level))
            logger.setLevel(logging.getLevelName(args.log_level))
            logger.info('main log level set to: ' + str(args.log_level))
            root_logger.info('root log level set to: ' + str(args.log_level))
        except Exception as e:
            root_logger.exception(e)
            # NOTE The returning value is never used
            return 1

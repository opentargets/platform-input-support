import os, sys, errno
import csv
import configargparse
import logging
from opentargets_urlzsource import URLZSource

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

"""
This will create a singleton argument parser that is appropriately configured
with the various command line, environment, and ini/yaml file options.

"""


def setup_parser():
    p = configargparse.get_argument_parser(config_file_parser_class=configargparse.YAMLConfigFileParser)
    p.description = 'Open Targets platform input support'

    # argument to read config file
    p.add('-c', '--config', is_config_file=True,
        env_var="CONFIG", help='path to config file (YAML)')

    p.add('-gkey', '--google_credential_key',
        env_var="GOOGLE_APPLICATION_CREDENTIALS", help='The path were the JSON credential file is stored.')

    p.add('-gb', '--google_bucket', help='Copy the files from the output directory to a specific google bucket')

    p.add('-o', '--output_dir',
        env_var="OT_OUTPUT_DIR", help='By default, the files are generated in the root directory')

    # argument to run the script using thread
    p.add('-t', '--thread', env_var="OT_THREAD", action='store_true', help='Run the script with thread')

    p.add('-s', '--suffix', env_var="OT_SUFFIX_INPUT",
          action='store', help='The default suffix is yyyy-mm-dd')

    p.add('-steps', action='store',nargs='+',
           help='Run a specific list of sections of the config file. Eg\n annotations annotations_from_buckets'
         )

    p.add('-exclude', action='store',nargs='+',
           help='Exclude a specific list of sections of the config file. Eg\n annotations annotations_from_buckets'
         )

    p.add('--skip', action='store_true', help='Skip the errors and just report them')

    p.add('-l','--list_steps', action='store_true', help='List of steps callable')

    # logging
    p.add("--log-level", help="set the log level",
        env_var="LOG_LEVEL", action='store', default='INFO')
    p.add("--log-config", help="logging configuration file",
        env_var="LOG_CONFIG", action='store', default='resources/logging.ini')

    return p


def get_args():
    p = configargparse.get_argument_parser()
    #dont use parse_args because that will error
    #if there are extra arguments e.g. for plugins
    args = p.parse_known_args()[0]

    #output all configuration values, useful for debugging
    p.print_values()

    return args


def get_input_file(input_filename, default_name_file):
    if input_filename is None:
        return default_name_file

    # check the file exists
    if not os.path.isfile(input_filename):
        raise IOError(
            errno.ENOENT, os.strerror(errno.ENOENT), ' The input file does not exists: %s' % input_filename)
    else:
        return input_filename


def get_list_of_file_download(config_file, headers):
    number_elem = len(headers)
    result = {}
    with URLZSource(config_file).open() as source:
        for i, row in enumerate(csv.DictReader(source, fieldnames=headers), start=1):
                if len(row) != number_elem:
                   raise ValueError('File format unexpected at line %d.' % i)

                for item in row:
                    result[item] = row[item]
                yield result


def setBasicConfigLog():
    logFilename = os.path.join(BASE_DIR, 'log/output.log')
    logging.basicConfig(level=logging.INFO, filename=logFilename, format= '%(name)-12s: %(levelname)-8s %(message)s',
     datefmt='%H:%M:%S')

    # set up logging to console
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logger = logging.getLogger(__name__)
    return logger

def set_up_logging(args):
    #set up logging
    logger = None
    if args.log_config:
        if os.path.isfile(args.log_config) and os.access(args.log_config, os.R_OK):
            logging.config.fileConfig(os.path.join(BASE_DIR, args.log_config), disable_existing_loggers=False)
            logger = logging.getLogger(__name__+".main()")
        else:
            logger = setBasicConfigLog()
            logger.warning("unable to read file {}".format(args.log_config))

    else:
        logger= setBasicConfigLog

    if args.log_level:
        try:
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.getLevelName(args.log_level))
            logger.setLevel(logging.getLevelName(args.log_level))
            logger.info('main log level set to: '+ str(args.log_level))
            root_logger.info('root log level set to: '+ str(args.log_level))
        except Exception, e:
            root_logger.exception(e)
            return 1

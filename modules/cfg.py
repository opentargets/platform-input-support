import os, sys, errno
import csv
import configargparse
from common import URLZSource

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

    p.add('-i', '--input_file',
        env_var="OT_INPUT_FILE", help='By default the file ROOT_DIR/annotations_input.csv will be loaded')

    p.add('-gkey', '--google_credential_key',
        env_var="GOOGLE_APPLICATION_CREDENTIALS", help='The path were the JSON credential file is stored.')

    p.add('-gb', '--google_bucket', help='Copy the files from the output directory to a specific google bucket')

    p.add('-o', '--output_dir',
        env_var="OT_OUTPUT_DIR", help='By default, the files are generated in the root directory')

    # argument to run the script using thread
    p.add('-t', '--thread', env_var="OT_THREAD", action='store_true', help='Run the script with thread')

    p.add('-s', '--suffix', env_var="OT_SUFFIX_INPUT",
          action='store', help='The default suffix is yyyy-mm-dd')

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


def get_output_dir(output_dir, default_output_dir):
    if output_dir is None:
        output_dir = default_output_dir
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    except OSError:
        sys.exit('Fatal: output directory "' + output_dir + '" does not exist and cannot be created')

    return output_dir

def get_list_of_file_download(config_file):
    headers = ["URI", "output_filename", "resource"]
    with URLZSource(config_file).open() as source:
        for i, row in enumerate(csv.DictReader(source, fieldnames=headers), start=1):
                if len(row) != 3:
                   raise ValueError('File format unexpected at line %d.' % i)

                yield dict(uri=row["URI"],
                           output_filename=row["output_filename"],
                           step=row["resource"],
                )
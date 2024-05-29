# Custom modules
import logging.config
import sys

# Custom modules
from platform_input_support.modules import cfg
from platform_input_support.manifest import get_manifest_service
from platform_input_support.modules.common.YAMLReader import YAMLReader, YAMLReaderException
from platform_input_support.modules.RetrieveResource import RetrieveResource

logger = logging.getLogger(__name__)


class PISRunnerException(Exception):
    """Platform input support exception"""


def print_list_steps(keys_list):
    """ Lists of the steps available defined inside the config yaml file. """
    keys_list.remove("config")
    list_steps = '\n\t'.join(keys_list)
    list_steps = 'List of steps available:\n\t' + list_steps
    print(list_steps)


# This procedure reads the config file and the args and runs the plugins requested.
def main():
    logger.debug("Setting up configuration parser")
    cfg.setup_parser()
    logger.debug("Get command line arguments")
    args = cfg.get_args()
    logger.debug("Prepare YAML reader for configuration file")
    try:
        yaml = YAMLReader(args.config)
        logger.debug("Read configuration file")
        yaml_dict = yaml.read_yaml()
        print_list_steps(yaml.get_list_keys())
    except YAMLReaderException as err:
        message = f"When trying to read the YAML config, the following error occurred '{err}'"
        logger.error(message)
        raise PISRunnerException(message) from err
    cfg.set_up_logging(args)

    # Resources retriever
    resources = RetrieveResource(args, yaml_dict)
    # Session's Manifest
    manifest_config = yaml_dict
    manifest_config.update({"output_dir": resources.output_dir_prod})
    # Initialize the manifest service
    _ = get_manifest_service(args, manifest_config)
    resources.run()


if __name__ == '__main__':
    main()

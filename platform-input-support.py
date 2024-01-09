# Custom modules
import logging.config

# Custom modules
from modules import cfg
from manifest import get_manifest_service
from modules.common.YAMLReader import YAMLReader
from modules.RetrieveResource import RetrieveResource

logger = logging.getLogger(__name__)


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
    yaml = YAMLReader(args.config)
    logger.debug(f"Read configuration file")
    yaml_dict = yaml.read_yaml()
    print_list_steps(yaml.get_list_keys())
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

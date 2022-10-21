# Custom modules
import logging.config

# Custom modules
import modules.cfg as cfg
import manifest
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
    cfg.setup_parser()
    args = cfg.get_args()
    yaml = YAMLReader(args.config)
    yaml_dict = yaml.read_yaml()
    print_list_steps(yaml.get_list_keys())
    cfg.set_up_logging(args)

    # Session's Manifest
    manifest_service = manifest.get_manifest_service(args, yaml_dict)
    # Resources retriever
    resources = RetrieveResource(args, yaml_dict)
    resources.run()


if __name__ == '__main__':
    main()

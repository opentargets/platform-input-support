# Custom modules
import logging.config

# Custom modules
import modules.cfg as cfg
from manifest import get_manifest_service, ManifestStatus
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
    manifest_service = get_manifest_service(args, manifest_config)
    try:
        resources.run()
    except Exception as e:
        manifest_service.manifest.status_completion = ManifestStatus.FAILED
        manifest_service.manifest.msg_completion = f"COULD NOT complete the data collection session due to '{e}'"
    if not manifest_service.are_all_steps_complete(manifest_service.manifest.steps.values()):
        manifest_service.manifest.status_completion = ManifestStatus.FAILED
        manifest_service.manifest.msg_completion = f"COULD NOT complete data collection for one or more steps"
    # TODO - Pipeline level VALIDATION
    if manifest_service.manifest.status_completion != ManifestStatus.FAILED:
        manifest_service.manifest.status_completion = ManifestStatus.COMPLETED
        manifest_service.manifest.msg_completion = f"All steps completed their data collection"
    else:
        logger.error(manifest_service.manifest.msg_completion)
    manifest_service.persist()


if __name__ == '__main__':
    main()

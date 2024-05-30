# Custom modules
from loguru import logger

from platform_input_support.logger import Logger
from platform_input_support.manifest import get_manifest_service

# Custom modules
from platform_input_support.modules import cfg
from platform_input_support.modules.common.yaml_reader import YAMLReader
from platform_input_support.modules.retrieve_resource import RetrieveResource


class PISRunnerError(Exception):
    """Platform input support exception."""


# This procedure reads the config file and the args and runs the plugins requested.
def main():
    Logger.init()

    cfg.setup_parser()
    args = cfg.get_args()

    yaml = YAMLReader(args.config)
    yaml_dict = yaml.read_yaml()

    Logger.config(yaml_dict)

    steps = yaml_dict['steps']
    step_names = ', '.join(list(steps.keys()))
    logger.info(f'{len(steps)} steps parsed from config: {step_names}')

    # Resources retriever
    resources = RetrieveResource(args, yaml_dict)
    # Session's Manifest
    manifest_config = yaml_dict
    manifest_config.update({'output_dir': resources.output_dir_prod})
    # Initialize the manifest service
    _ = get_manifest_service(args, manifest_config)
    resources.run()


if __name__ == '__main__':
    main()

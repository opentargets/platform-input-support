# Custom modules
from addict import Dict
from loguru import logger

from platform_input_support.config import config
from platform_input_support.logger import logger
from platform_input_support.manifest.services import get_manifest_service
from platform_input_support.modules.retrieve_resource import RetrieveResource


class PISRunnerError(Exception):
    """Platform input support exception."""


def main():
    logger.info('starting platform input support')

    steps = config.get('steps', {})
    step_names = ', '.join(list(steps.keys()))
    logger.info(f'{len(steps)} steps parsed from config: {step_names}')

    # mock stuff here to make things work again - This is temporary
    yaml_dict = config
    yaml_dict = Dict(yaml_dict)
    yaml_dict.manifest = {'file_name': 'manifest.json'}
    config['output_dir'] = './output'
    config['force_clean'] = False

    # Resources retriever
    resources = RetrieveResource(config, yaml_dict)
    # Session's Manifest
    manifest_config = yaml_dict
    manifest_config.update({'output_dir': resources.output_dir_prod})
    # Initialize the manifest service
    _ = get_manifest_service(config, manifest_config)
    resources.run()


if __name__ == '__main__':
    main()

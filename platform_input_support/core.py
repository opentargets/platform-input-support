# Custom modules
from importlib.metadata import version

from loguru import logger

from platform_input_support.config import config
from platform_input_support.logger import Logger
from platform_input_support.modules.services import google_service

# from platform_input_support.step.step_repository import StepRepository


class PISRunnerError(Exception):
    """Platform input support exception."""


def main():
    Logger(config.settings)
    logger.debug('logger configured')

    logger.info(f'starting platform input support v{version("platform_input_support")}')

    # step_repository = StepRepository()
    # step_repository.register_steps()

    # step_repository.run()

    # # # Resources retriever
    # resources = RetrieveResource(yaml_dict['settings'], yaml_dict)
    # # # Session's Manifest
    # manifest_config = yaml_dict
    # print(yaml_dict)
    # manifest_config.update({'output_dir': resources.output_dir_prod})
    # _ = get_manifest_service(yaml_dict['settings'], manifest_config)


if __name__ == '__main__':
    main()

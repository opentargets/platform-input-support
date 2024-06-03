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


if __name__ == '__main__':
    main()

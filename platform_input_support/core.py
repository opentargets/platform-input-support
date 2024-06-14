# Custom modules
from importlib.metadata import version

from loguru import logger

from platform_input_support.config import config, tasks
from platform_input_support.logger import Logger
from platform_input_support.step import Step


class PISRunnerError(Exception):
    """Platform input support exception."""


def main():
    logger.info(f'starting platform input support v{version("platform_input_support")}')

    Logger(config)
    logger.debug('logger configured')

    step = Step(config.step, tasks)
    step.run()


if __name__ == '__main__':
    main()

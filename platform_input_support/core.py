# Custom modules
from importlib.metadata import version

from loguru import logger

from platform_input_support.config import config, tasks
from platform_input_support.step import Step
from platform_input_support.util.logger import init_logger


class PISRunnerError(Exception):
    """Platform input support exception."""


def main():
    init_logger(config)
    logger.info(f'starting platform input support v{version("platform_input_support")}')

    step = Step(config.step, tasks)
    step.run()


if __name__ == '__main__':
    main()

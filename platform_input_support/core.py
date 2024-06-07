# Custom modules
from importlib.metadata import version

from loguru import logger

from platform_input_support.action.action_repository import ActionRepository
from platform_input_support.config import config, steps
from platform_input_support.logger import Logger


class PISRunnerError(Exception):
    """Platform input support exception."""


def main():
    Logger(config)

    logger.debug('logger configured')
    logger.info(f'starting platform input support v{version("platform_input_support")}')

    action_repository = ActionRepository()
    action_repository.register_actions()

    step = steps[config.step]

    for action in step.actions:
        logger.debug(f'running action {action}')

        new_action = action_repository.actions[action.name](action.config)

        new_action.run()


if __name__ == '__main__':
    main()

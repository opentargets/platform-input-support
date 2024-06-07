# Custom modules
from importlib.metadata import version

from loguru import logger

from platform_input_support.action.action_repository import ActionRepository
from platform_input_support.config import config, steps
from platform_input_support.helpers.google import google
from platform_input_support.logger import Logger


class PISRunnerError(Exception):
    """Platform input support exception."""


def main():
    logger.info(f'starting platform input support v{version("platform_input_support")}')

    Logger(config)
    logger.debug('logger configured')

    action_repository = ActionRepository()
    action_repository.register_actions()

    step = steps[config.step]

    for action_mapping in step.actions:
        logger.debug(f'running action {action_mapping.name}')

        action = action_repository.actions[action_mapping.name](action_mapping.config)
        action.run()

        print(action._report)


if __name__ == '__main__':
    main()

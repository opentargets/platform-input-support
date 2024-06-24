from importlib.metadata import version

from loguru import logger

from platform_input_support.config import init_config, settings, task_definitions
from platform_input_support.helpers import init_google_helper
from platform_input_support.manifest.manifest import Manifest
from platform_input_support.step import Step
from platform_input_support.task import init_task_registry
from platform_input_support.util.fs import check_dir
from platform_input_support.util.logger import init_logger


def main():
    logger.info(f'starting platform input support v{version("platform_input_support")}')

    # initialize config
    init_config()

    # initialize logger
    init_logger(settings().log_level)

    # initialize google helper
    init_google_helper()

    # initialize task registry
    init_task_registry()

    # initialize task definitions for the designated step
    task_definitions()

    # check conditions in the work directory
    check_dir(settings().work_dir)

    # instantiate and run the step given as argument
    step = Step(settings().step)
    step.run()

    print('step manifest:', step._manifest.model_dump_json(indent=2))


if __name__ == '__main__':
    main()

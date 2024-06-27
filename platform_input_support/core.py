from importlib.metadata import version

from loguru import logger

from platform_input_support.config import init_config, settings
from platform_input_support.helpers import init_google_helper
from platform_input_support.manifest.manifest import Manifest
from platform_input_support.step import Step
from platform_input_support.task import init_task_registry
from platform_input_support.util.fs import check_dir
from platform_input_support.util.logger import init_logger


def main():
    logger.info(f'starting platform input support v{version("platform_input_support")}')

    init_config()
    init_logger(settings().log_level)
    init_google_helper()
    init_task_registry()

    check_dir(settings().work_dir)

    step = Step(settings().step)
    step.execute()

    manifest = Manifest()
    manifest.update_step(step)
    manifest.complete()


if __name__ == '__main__':
    main()

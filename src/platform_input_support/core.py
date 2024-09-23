"""Main entry point for the platform input support tool."""

import ssl
import sys
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
    """Main entry point for the platform input support tool.

    This function will run when the package is invoked from the command line. It will:

    1. Initialize the configuration.
    2. Make some checks on the working directory.
    3. Initialize the logger.
    4. Initialize the Google Cloud helper.
    5. Initialize the task registry, loading all tasks in the tasks module.
    6. Create a step object based on the configuration.
    7. Execute the step.
    8. Create a manifest object and update it with the step information.
    9. Complete the manifest, saving it both locally and on Google Cloud.
    """
    logger.info(f'starting platform input support v{version("platform_input_support")}')

    init_config()
    check_dir(settings().work_dir)

    init_logger(settings().log_level)
    init_google_helper()
    init_task_registry()

    logger.debug(f'using {ssl.OPENSSL_VERSION}')
    logger.debug(f'running with {settings().pool} worker processes')

    step = Step(settings().step)
    step.execute()

    manifest = Manifest()
    manifest.update_step(step)
    manifest.complete()

    if not manifest.is_completed():
        logger.error('step did not complete successfully')
        sys.exit(1)


if __name__ == '__main__':
    main()

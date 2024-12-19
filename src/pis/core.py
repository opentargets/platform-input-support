"""Main entry point for the PIS tool."""

import ssl
import sys
from importlib.metadata import version

from loguru import logger

from pis.config import init_config, settings
from pis.manifest.manifest import Manifest
from pis.step import Step
from pis.task import init_task_registry
from pis.util.fs import check_dir
from pis.util.logger import init_logger


def main():
    """Main entry point for the PIS tool.

    This function will run when the package is invoked from the command line. It will:

    1. Initialize the configuration.
    2. Make some checks on the working directory.
    3. Initialize the logger.
    4. Initialize the task registry, loading all tasks in the tasks module.
    5. Create a step object based on the configuration.
    6. Execute the step.
    7. Create a manifest object and update it with the step information.
    8. Complete the manifest, saving it both locally and remotely (if configured).
    """
    logger.info(f'starting PIS v{version('pis')}')

    init_config()
    check_dir(settings().work_dir)

    init_logger(settings().log_level)
    init_task_registry()

    logger.debug(f'using {ssl.OPENSSL_VERSION}')
    logger.debug(f'running with {settings().pool} worker processes')

    step = Step(settings().step)
    step.execute()

    manifest = Manifest()
    manifest.update_step(step)
    manifest.complete()

    if not manifest.run_ok():
        logger.error('step did not complete successfully')
        sys.exit(1)

    if not manifest.is_completed():
        logger.warning('there are incomplete steps in the manifest')
    else:
        logger.success('all steps are now complete!')


if __name__ == '__main__':
    main()

from importlib.metadata import version

from loguru import logger

from platform_input_support.config import settings, task_definitions
from platform_input_support.manifest import Manifest
from platform_input_support.step import Step
from platform_input_support.util.logger import init_logger
from platform_input_support.util.misc import check_dir


def main():
    print(settings)
    init_logger(settings.log_level)
    logger.info(f'starting platform input support v{version("platform_input_support")}')
    check_dir(settings.work_dir)

    manifest = Manifest()

    step_name = settings.step
    step_manifest = manifest.get_step_manifest(step_name)
    step = Step(step_name, task_definitions=task_definitions, manifest=step_manifest)
    step.run()

    manifest.end(step_manifest)


if __name__ == '__main__':
    main()

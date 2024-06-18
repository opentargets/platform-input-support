# Custom modules
from importlib.metadata import version

from loguru import logger

from platform_input_support.config import config, task_mappings
from platform_input_support.manifest import Manifest
from platform_input_support.step import Step
from platform_input_support.util.logger import init_logger


def main():
    init_logger(config)
    logger.info(f'starting platform input support v{version("platform_input_support")}')

    manifest = Manifest()

    step_name = config.step
    step_manifest = manifest.get_step_manifest(step_name)
    step = Step(config.step, task_mappings=task_mappings, manifest=step_manifest)
    step.run()

    manifest.end(step_manifest)


if __name__ == '__main__':
    main()

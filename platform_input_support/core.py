from importlib.metadata import version

from loguru import logger

from platform_input_support.config import settings
from platform_input_support.step import Step
from platform_input_support.util.logger import init_logger
from platform_input_support.util.misc import check_dir


def main():
    init_logger(settings.log_level)
    logger.info(f'starting platform input support v{version("platform_input_support")}')
    check_dir(settings.work_dir)

    step = Step(settings.step)
    step.run()

    print('Done! Step manifest:', step._manifest.model_dump_json(indent=2))


if __name__ == '__main__':
    main()

import sys
from pathlib import Path

from loguru import logger

from platform_input_support.config.models import ConfigMapping

__all__ = ['logger']


class Logger:
    def __init__(self, config: ConfigMapping) -> None:
        log_level = config.log_level
        log_filename = Path(config.output_path) / 'output.log'

        handlers = [
            {
                'sink': sys.stdout,
                'level': log_level,
            },
            {
                'sink': log_filename,
                'level': log_level,
                'serialize': True,
            },
        ]

        logger.configure(handlers=handlers)

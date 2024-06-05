import sys
from pathlib import Path

from loguru import logger

from platform_input_support.config.models import SettingsModel

__all__ = ['logger']


class Logger:
    def __init__(self, settings: SettingsModel) -> None:
        log_level = settings.log_level
        log_filename = Path(settings.output_path) / 'output.log'

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

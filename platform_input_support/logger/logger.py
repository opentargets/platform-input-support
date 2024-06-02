import logging
import logging.config
import logging.handlers
import sys

from loguru import logger as _logger

from platform_input_support.config import config
from platform_input_support.config.models import SettingsModel

__all__ = ['logger']


class CustomFormatter(logging.Formatter):
    def format(self, record):
        saved_name = record.name
        parts = record.name.split('.')
        if len(parts) and parts[0] == 'platform_input_support':
            parts = parts[1:]

        record.name = '.'.join(parts)
        result = super().format(record)
        record.name = saved_name
        return result


class Logger:
    def __init__(self, settings: SettingsModel) -> None:
        log_level = settings.log_level
        log_filename = settings.log_filename

        handlers = [
            {
                'sink': sys.stdout,
                'level': log_level,
            },
        ]

        if log_filename:
            handlers.append(
                {
                    'sink': log_filename,
                    'level': log_level,
                    'serialize': True,
                }
            )

        _logger.configure(handlers=handlers)


log = Logger(config.settings)
logger = _logger
logger.debug('logger configured')

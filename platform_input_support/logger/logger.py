import logging
import logging.config
import logging.handlers
import sys

from loguru import logger as _logger

from platform_input_support.config import config

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
    def __init__(self, config: dict) -> None:
        log_level = config.get('log_level', 'DEBUG')
        log_filename = config.get('log_filename')

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


log = Logger(config)
logger = _logger
logger.debug('logger configured')

import logging
import logging.config
import logging.handlers
import sys

from loguru import logger


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
    @classmethod
    def init(cls):
        handlers = [
            {
                'sink': sys.stdout,
                'level': 'DEBUG',
            },
        ]

        logger.configure(handlers=handlers)
        logger.debug('logger initialized')

    @classmethod
    def config(cls, config: dict) -> None:
        log_level = config.get('log_level')
        log_filename = config.get('log_filename')

        if log_level is None and log_filename is None:
            logger.info('No log configuration found, keeping defaults')
            return

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

        logger.remove()
        logger.configure(handlers=handlers)
        logger.debug('logger configured')

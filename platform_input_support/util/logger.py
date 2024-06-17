import sys
from pathlib import Path

from loguru import logger

from platform_input_support.config.models import ConfigMapping


def init_logger(config: ConfigMapping) -> None:
    log_level = config.log_level
    log_filename = Path(config.output_path) / 'output.log'

    def format_log(record):
        task = '<y>{extra[task]}</>::' if record['extra'].get('task') else ''

        return (
            '<g>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | '
            '<lvl>{level: <8}</> | '
            f'{task}'
            '<c>{name}</>:<c>{function}</>:<c>{line}</>'
            ' - <lvl>{message}</>\n{exception}'
        )

    handlers = [
        {
            'sink': sys.stdout,
            'level': log_level,
            'format': format_log,
        },
        {
            'sink': log_filename,
            'level': log_level,
            'serialize': True,
        },
    ]

    logger.configure(handlers=handlers)
    logger.debug('logger configured')

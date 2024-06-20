import sys

from loguru import logger

from platform_input_support.util.misc import get_full_path


def init_logger(log_level: str) -> None:
    log_filename = get_full_path('output.log')

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

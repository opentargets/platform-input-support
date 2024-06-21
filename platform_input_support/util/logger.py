import sys
from types import TracebackType
from typing import TYPE_CHECKING

from loguru import logger

from platform_input_support.config import settings
from platform_input_support.util.fs import get_full_path

if TYPE_CHECKING:
    from platform_input_support.task import Task
from contextlib import contextmanager


def get_exception_info(record_exception) -> tuple[str, str, str]:
    name = '{name}'
    function = '{function}'
    line = '{line}'

    if record_exception is not None:
        tb: TracebackType
        _, _, tb = record_exception

        # go back in the stack to the first frame originated inside the app
        app_name = globals()['__package__'].split('.')[0]
        while tb.tb_next:
            next_name = tb.tb_next.tb_frame.f_globals.get('__name__', None)
            if app_name not in next_name:
                break
            name = next_name
            tb = tb.tb_next
        function = tb.tb_frame.f_code.co_name
        line = str(tb.tb_lineno)

    return name, function, line


def format_task_log(record):
    name, function, line = get_exception_info(record.get('exception'))

    return (
        '<g>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | '
        '<lvl>{level: <8}</> | '
        f'<c>{name}</>:<c>{function}</>:<c>{line}</>'
        ' - <lvl>{message}</>'
    )


@contextmanager
def task_logging(task: 'Task'):
    with logger.contextualize(task=task.name):
        sink_task = lambda message: task._manifest.log.append(message)
        logger.add(
            sink=sink_task,
            filter=lambda record: record['extra'].get('task') == task.name,
            format=format_task_log,
            level=settings.log_level,
        )

        yield


def init_logger(log_level: str) -> None:
    log_filename = get_full_path('output.log')

    def format_log(record):
        name, function, line = get_exception_info(record.get('exception'))
        task = '<y>{extra[task]}</>::' if record['extra'].get('task') else ''

        return (
            '<g>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | '
            '<lvl>{level: <8}</> | '
            f'{task}'
            f'<c>{name}</>:<c>{function}</>:<c>{line}</>'
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

    logger.remove()
    logger.configure(handlers=handlers)
    logger.debug('logger configured')

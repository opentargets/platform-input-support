import os
import sys
from pathlib import Path

import pytest
from loguru import logger

from platform_input_support.util.logger import get_exception_info, get_format_log, init_logger, task_logging


@pytest.fixture
def show_exceptions_with_flag():
    original = os.environ.get('PIS_SHOW_EXCEPTIONS', '')
    os.environ['PIS_SHOW_EXCEPTIONS'] = 'true'
    yield
    os.environ['PIS_SHOW_EXCEPTIONS'] = original


@pytest.fixture
def config():
    os.environ['PIS_STEP'] = 'so'
    sys.argv = sys.argv[:1]  # remove any arguments passed to pytest
    from platform_input_support.config import settings

    settings()
    yield
    del os.environ['PIS_STEP']


def test_get_exception_info_with_none():
    assert get_exception_info(None) == ('{name}', '{function}', '{line}')


def test_get_exception_info_with_exception():
    try:
        raise ValueError('Test exception')
    except ValueError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        name, func, line = get_exception_info((exc_type, exc_value, exc_traceback))

        assert name and func and line
        assert line.isdigit()  # Line number should be a digit


def test_get_exception_info_with_deep_exception():
    def a():
        b()

    def b():
        Path('non_existent_file.txt').read_text()

    try:
        a()
    except FileNotFoundError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        name, func, line = get_exception_info((exc_type, exc_value, exc_traceback))

        assert name and func and line
        assert name == 'platform_input_support.util.logger_test'
        assert func == 'b'
        assert line.isdigit()  # Line number should be a digit


def test_get_format_log_returns_callable():
    assert callable(get_format_log())


def test_format_log_without_exception():
    formatter = get_format_log(include_task=False)
    record = {'extra': {}, 'message': 'Test message'}

    formatted = formatter(record)

    assert '{exception}' not in formatted


def test_format_log_with_show_exceptions_flag(show_exceptions_with_flag):
    formatter = get_format_log()
    record = {'extra': {}, 'message': 'Test message'}

    formatted = formatter(record)

    assert '{exception}' in formatted


def test_format_log_with_exception(monkeypatch):
    def mock_get_exception_info(*args, **kwargs):
        return ('MockName', 'MockFunction', 'MockLine')

    monkeypatch.setattr('platform_input_support.util.logger.get_exception_info', mock_get_exception_info)
    formatter = get_format_log()
    record = {'extra': {}, 'message': 'Test message', 'exception': 'Test exception'}

    formatted = formatter(record)

    assert '{exception}' not in formatted


def test_task_logging_context_manager(config):
    class TaskManifest:
        def __init__(self):
            self.log = []

    class Task:
        def __init__(self, name):
            self.name = name
            self._manifest = TaskManifest()

    task = Task('TestTask')

    with task_logging(task):  # type: ignore[arg-type]
        from loguru import logger

        assert len(task._manifest.log) == 0
        logger.info('Test message')
        assert len(task._manifest.log) == 1


def test_init_logger(monkeypatch, capsys, tmp_path):
    test_file_path = tmp_path / 'pis_test_output.log'
    monkeypatch.setattr('platform_input_support.util.logger.absolute_path', lambda x: test_file_path)

    init_logger('DEBUG')
    logger.info('Test info message')
    logger.debug('Test debug message')
    logger.trace('Test trace message')

    captured = capsys.readouterr()
    assert 'Test info message' in captured.out
    assert 'Test debug message' in captured.out
    assert 'Test trace message' not in captured.out

    test_content = Path.read_text(test_file_path)
    assert os.path.exists(test_file_path)
    assert 'Test info message' in test_content
    assert 'Test debug message' in test_content
    assert 'Test trace message' not in test_content

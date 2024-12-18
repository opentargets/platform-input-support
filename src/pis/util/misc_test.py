from datetime import datetime

import pytest

from pis.util.misc import date_str, real_name


@pytest.fixture
def mock_task_definition():
    class MockTaskDefinition:
        name = 'Test TaskDefinition One'

    return MockTaskDefinition()


@pytest.fixture
def mock_task():
    class MockTask:
        name = 'Test Task One'

    return MockTask()


def test_date_str():
    test_datetime = datetime(2023, 1, 1, 12, 0, 0)
    assert date_str(test_datetime) == '2023-01-01 12:00:00'


def test_date_str_with_none():
    assert date_str(None) == datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def test_real_name_with_task(mock_task):
    assert real_name(mock_task) == 'Test'


def test_real_name_with_task_definition(mock_task_definition):
    assert real_name(mock_task_definition) == 'Test'

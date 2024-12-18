"""Misc utility functions."""

from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pis.config.models import BaseTaskDefinition
    from pis.task import Task


def date_str(d: datetime | None = None) -> str:
    """Return a string representation of a datetime object.

    :param d: datetime object to convert to string.
    :type d: datetime | None, optional
    :return: string representation of the datetime object.
    :rtype: str
    """
    return (d or datetime.now()).strftime('%Y-%m-%d %H:%M:%S')


def real_name(t: 'Task | BaseTaskDefinition') -> str:
    """Return the real name of a task.

    The naming convention is snake_case for task names.

    The real name of a task is the first word of the name. It determines the type of
    task that will be spawned when the task is run, so the name should exist in the
    task registry (a task with that name must exist in the tasks module).

    :param t: Task or TaskDefinition object to get the real name of.
    :type t: Task | BaseTaskDefinition
    :return: The real name of the task.
    :rtype: str
    """
    return t.name.split(' ')[0]


def list_str(a_list: Iterable[Any], dict_values: bool = False) -> str:
    """Return a string representation of a list or dictionary.

    :param a_list: The list or dictionary to convert to a string.
    :type a_list: Iterable[Any]
    :param dict_values: Whether to include the values of a dictionary.
    :type dict_values: bool, optional
    :return: A string representation of the list or dictionary.
    :rtype: str
    """
    if isinstance(a_list, list):
        return ', '.join(map(str, a_list))
    elif isinstance(a_list, dict):
        if dict_values:
            return ', '.join([f'{k}={v}' for k, v in a_list.items()])
        else:
            return ', '.join(list(a_list))
    elif isinstance(a_list, str):
        return a_list
    return str(a_list)

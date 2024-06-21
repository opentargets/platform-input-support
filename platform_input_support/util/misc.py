from datetime import datetime
from typing import TYPE_CHECKING, Any
from xmlrpc.client import Boolean

if TYPE_CHECKING:
    from platform_input_support.config.models import TaskDefinition
    from platform_input_support.task import Task


def date_str(d: datetime) -> str:
    return d.strftime('%Y-%m-%d %H:%M:%S')


def real_name(t: 'Task | TaskDefinition') -> str:
    if getattr(t, 'name', None):
        return t.name.split(' ')[0]
    elif isinstance(t, dict):
        name = t.get('name')
        if name:
            return name.split(' ')[0]
    raise ValueError(f'invalid task definition: {t}')


def list_str(a_list: Any, dict_values: Boolean = False) -> str:
    if isinstance(a_list, list):
        return ', '.join(map(str, a_list))
    elif isinstance(a_list, dict):
        if dict_values:
            return ', '.join([f'{k}={v}' for k, v in a_list.items()])
        else:
            return ', '.join([k for k, v in a_list.items()])
    elif isinstance(a_list, str):
        return a_list
    return str(a_list)

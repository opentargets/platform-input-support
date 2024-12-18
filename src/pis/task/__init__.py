"""Task module."""

from pis.task.task import Pretask, Task
from pis.task.task_registry import TaskRegistry
from pis.util.errors import PISError

_task_registry: TaskRegistry | None = None


def init_task_registry():
    """Initialize the task registry."""
    global _task_registry  # noqa: PLW0603
    if _task_registry is None:
        _task_registry = TaskRegistry()
        _task_registry.register_tasks()


def task_registry():
    """Return the task registry.

    The task registry must be initialized explicitly by calling the `init_task_registry`
    function before trying to access it. If it is not initialized, a PISError is raised.

    :raises PISError: If the task registry is not initialized.
    :return: The task registry.
    :rtype: TaskRegistry
    """
    if _task_registry is None:
        raise PISError('task registry not initialized')

    assert _task_registry is not None
    return _task_registry

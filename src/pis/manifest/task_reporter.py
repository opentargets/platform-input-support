"""TaskReporter class and report decorator for logging and updating tasks in the manifest."""

import sys
from datetime import UTC, datetime
from functools import wraps
from typing import TYPE_CHECKING

from loguru import logger

from pis.config import settings
from pis.manifest.models import Resource, Result, TaskManifest
from pis.util.errors import TaskAbortedError

if TYPE_CHECKING:
    from pis.task import Task


class TaskReporter:
    """Class for logging and updating tasks in the manifest."""

    def __init__(self, name: str):
        self.name = name
        self._manifest: TaskManifest
        self._resources: list[Resource] = []

    def staged(self, log: str):
        """Set the task result to STAGED."""
        self._manifest.result = Result.STAGED
        self._manifest.staged = datetime.now(UTC)
        self._manifest.elapsed = (self._manifest.staged - self._manifest.created).total_seconds()
        logger.success(f'task staged: ran for {self._manifest.elapsed:.2f}s')

    def validated(self, log: str, resource: Resource | None = None):
        """Set the task result to VALIDATED."""
        self._manifest.result = Result.VALIDATED
        if resource:
            self._resources.append(resource.make_absolute())
        logger.success(f'task validated: {log}')

    def completed(self, log: str, resource: Resource | None = None):
        """Set the task result to COMPLETED."""
        self._manifest.result = Result.COMPLETED
        if resource:
            self._resources.append(resource.make_absolute())
        logger.success(f'task completed: {log}')

    def failed(self, error: Exception, where: str):
        """Set the task result to FAILED."""
        self._manifest.result = Result.FAILED
        logger.opt(exception=sys.exc_info()).error(f'task failed {where}: {error}')

    def aborted(self):
        """Set the task result to ABORTED."""
        self._manifest.result = Result.ABORTED
        logger.warning('task aborted')


def report(func):
    """Decorator for logging and updating tasks in the manifest."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            if func.__name__ == 'run':
                logger.info('task run started')
                # add task definition to the manifest
                self._manifest = self._manifest.model_copy(update={'definition': self.definition.__dict__}, deep=True)
            elif func.__name__ == 'validate':
                logger.info('task validation started')
            elif func.__name__ == 'upload':
                logger.info('task upload started')

            result: Task = func(self, *args, **kwargs)

            if func.__name__ == 'run':
                self.staged(result.name)
            elif func.__name__ == 'validate':
                self.validated(result.name, result.resource if not settings().remote_uri else None)
            elif func.__name__ == 'upload':
                self.completed(result.name, result.resource)
            return result
        except Exception as e:
            kwargs['abort'].set()
            if isinstance(e, TaskAbortedError):
                self.aborted()
            else:
                self.failed(e, func.__name__)

    return wrapper

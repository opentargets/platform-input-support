import sys
from functools import wraps
from typing import TYPE_CHECKING

from loguru import logger

from platform_input_support.manifest.models import Result, StepManifest

if TYPE_CHECKING:
    from platform_input_support.task import Task


class StepReporter:
    def __init__(self, name: str):
        self.name = name
        self._manifest = StepManifest(name=self.name)

    def staged(self, log: str):
        self._manifest.result = Result.STAGED
        msg = f'step staged: {log}'
        self._manifest.log.append(msg)
        logger.info(msg)

    def completed(self, log: str):
        self._manifest.result = Result.COMPLETED
        msg = f'step completed: {log}'
        self._manifest.log.append(msg)
        logger.success(msg)

    def validated(self, log: str):
        self._manifest.result = Result.VALIDATED
        msg = f'step validated: {log}'
        self._manifest.log.append(msg)
        logger.success(msg)

    def failed(self, log: str):
        self._manifest.result = Result.FAILED
        msg = f'step failed: {log}'
        self._manifest.log.append(msg)
        logger.opt(exception=sys.exc_info()).error(msg)

    def attach_manifest(self, task: 'Task'):
        self._manifest.tasks.append(task._manifest)
        msg = f'task {task.name} {task._manifest.result}'
        self._manifest.log.append(msg)
        logger.info(msg)

    def upsert_task_manifests(self, tasks: list['Task']):
        for task in tasks:
            inserted = False
            for i, t in enumerate(self._manifest.tasks):
                if t.name == task.name:
                    self._manifest.tasks[i] = task._manifest
                    self._manifest.resources.extend(task._resources)
                    inserted = True
                    break
            if not inserted:
                self._manifest.tasks.append(task._manifest)


def report(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            if func.__name__ == '_run':
                logger.info('step run started')
            elif func.__name__ == '_validate':
                logger.info('step validation started')
            elif func.__name__ == '_upload':
                logger.info('step upload started')

            result = func(self, *args, **kwargs)

            # update task manifest
            self.upsert_task_manifests(result)

            if func.__name__ == '_run':
                self.staged(f'ran {len(result)} tasks')
            elif func.__name__ == '_validate':
                self.validated(f'validated {len(result)} tasks')
            elif func.__name__ == '_upload':
                self.completed(f'uploaded {len(result)} tasks')
            return result
        except Exception as e:
            kwargs['abort'].set()
            self.failed(f'{func.__name__} failed: {e}')

    return wrapper

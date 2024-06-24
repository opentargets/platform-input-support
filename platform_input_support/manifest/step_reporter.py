import sys

from git import TYPE_CHECKING
from loguru import logger

from platform_input_support.manifest.models import Result, StepManifest

if TYPE_CHECKING:
    from platform_input_support.task import Task


class StepReporter:
    def __init__(self, name: str):
        self.name = name
        self._manifest = StepManifest(name=self.name)

    def stage(self, log: str):
        self._manifest.result = Result.STAGED
        msg = f'step staged: {log}'
        self._manifest.log.append(msg)
        logger.info(msg)

    def complete(self, log: str):
        self._manifest.result = Result.COMPLETED
        msg = f'step completed: {log}'
        self._manifest.log.append(msg)
        logger.success(msg)

    def validate(self, log: str):
        self._manifest.result = Result.VALIDATED
        msg = f'step validated: {log}'
        self._manifest.log.append(msg)
        logger.success(msg)

    def fail(self, log: str):
        self._manifest.result = Result.FAILED
        msg = f'step failed: {log}'
        self._manifest.log.append(msg)
        logger.opt(exception=sys.exc_info()).error(msg)

    def abort(self):
        self._manifest.result = Result.ABORTED
        msg = 'step aborted'
        self._manifest.log.append(msg)
        logger.warning(msg)

    def add_task(self, task: 'Task'):
        self._manifest.tasks.append(task._manifest)
        msg = f'task {task.name} {task._manifest.result}'
        self._manifest.log.append(msg)
        logger.info(msg)

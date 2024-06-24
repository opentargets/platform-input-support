import sys
from functools import wraps

from loguru import logger

from platform_input_support.manifest.models import Result, TaskManifest


class TaskReporter:
    def __init__(self, name: str):
        self.name = name
        self._manifest: TaskManifest

    def stage(self, log: str):
        self._manifest.result = Result.STAGED
        logger.info(f'task staged: {log}')

    def complete(self, log: str):
        self._manifest.result = Result.COMPLETED
        logger.success(f'task completed: {log}')

    def validate(self, log: str):
        self._manifest.result = Result.VALIDATED
        logger.success(f'task validated: {log}')

    def fail(self, error: Exception):
        self._manifest.result = Result.FAILED
        logger.opt(exception=sys.exc_info()).error(f'task failed: {error}')

    def abort(self):
        self._manifest.result = Result.ABORTED
        logger.warning('task aborted')


def report_to_manifest(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            if func.__name__ == 'run':
                # add task definition to the manifest
                self._manifest = self._manifest.model_copy(update={'definition': self.definition.__dict__}, deep=True)

            result = func(self, *args, **kwargs)

            if func.__name__ == 'run':
                self.stage(result)
            elif func.__name__ == 'upload':
                self.complete(result)
            elif func.__name__ == 'validate':
                self.validate(result)
            return result
        except Exception as e:
            self.fail(f'{func.__name__} failed: {e}')
            raise

    return wrapper

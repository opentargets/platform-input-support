import sys
from functools import wraps

from loguru import logger

from platform_input_support.manifest.models import Status, TaskManifest


class TaskReporter:
    def __init__(self, name: str):
        self.name = name
        self._manifest: TaskManifest

    def start(self):
        logger.info('task started')

    def complete(self, log: str):
        self._manifest.status = Status.COMPLETED
        logger.success(f'task completed: {log}')

    def fail(self, error: Exception):
        self._manifest.status = Status.FAILED
        logger.opt(exception=sys.exc_info()).error(f'task failed: {error}')

    def pass_validation(self, log: str):
        self._manifest.status = Status.VALIDATION_PASSED
        logger.success('validation passed')

    def fail_validation(self, error: Exception):
        self._manifest.status = Status.VALIDATION_FAILED
        logger.opt(exception=sys.exc_info()).error(f'failed validation: {error}')


def report_to_manifest(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            if func.__name__ == 'run':
                self.start()

                # add custom fields from definition to the manifest
                self._manifest = self._manifest.model_copy(update={'definition': self.definition.__dict__}, deep=True)

            result = func(self, *args, **kwargs)

            if func.__name__ == 'run':
                self.complete(result)
            elif func.__name__ == 'validate':
                self.pass_validation(result)
            return result
        except Exception as e:
            if func.__name__ == 'run':
                self.fail(e)
            elif func.__name__ == 'validate':
                self.fail_validation(e)

    return wrapper

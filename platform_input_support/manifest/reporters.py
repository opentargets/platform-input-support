import dataclasses
import sys
from functools import wraps
from importlib import import_module

from loguru import logger

from platform_input_support.manifest.models import Status, StepManifest, TaskManifest


class StepReporter:
    def __init__(self, name: str):
        self.name = name
        self._manifest = StepManifest(self.name)

    def start(self):
        logger.info(f'starting step {self.name}')
        self._manifest.status = Status.NOT_COMPLETED

    def complete(self):
        logger.success(f'step {self.name} completed')
        self._manifest.status = Status.COMPLETED

    def fail(self, error: Exception):
        logger.error(f'step {self.name} failed: {error}')
        self._manifest.log.append(str(error))
        self._manifest.status = Status.FAILED

    def validate(self):
        if self._manifest.status is Status.NOT_SET:
            if any(task.status is not Status.VALIDATION_PASSED for task in self._manifest.tasks):
                self._manifest.status = Status.FAILED

    # No typing here to avoid import mess, when https://peps.python.org/pep-0649/ comes out
    def add_task(self, task):
        self._manifest.tasks.append(task._manifest)


class TaskReporter:
    def __init__(self, name: str):
        self.name = name
        task_class = self.__class__
        task_class_name = self.__class__.__name__
        task_module = import_module(task_class.__module__)
        manifest_class_name = f'{task_class_name}Manifest'
        manifest_class: type[TaskManifest] = getattr(task_module, manifest_class_name, TaskManifest)
        self._manifest = manifest_class(self.name)

    def start(self):
        logger.info('starting task')
        self._manifest.status = Status.NOT_COMPLETED

    def complete(self, log: str):
        logger.success(f'task completed: {log}')
        self._manifest.log.append(log)
        self._manifest.status = Status.COMPLETED

    def fail(self, error: Exception):
        logger.opt(exception=sys.exc_info()).error(f'task failed: {error}')
        self._manifest.log.append(str(error))
        self._manifest.status = Status.FAILED

    def pass_validation(self, log: str):
        logger.success('validation passed')
        self._manifest.log.append(log)
        self._manifest.status = Status.VALIDATION_PASSED

    def fail_validation(self, error: Exception):
        logger.error(f'failed validation: f{error}')
        self._manifest.log.append(str(error))
        self._manifest.status = Status.VALIDATION_FAILED

    def append_log(self, log: str):
        logger.info(log)
        self._manifest.log.append(log)

    def set_field(self, field_name: str, value: str):
        setattr(self._manifest, field_name, value)


def report_to_manifest(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            if func.__name__ == 'run':
                self.start()

                # add custom fields from config to the manifest
                for k, v in dataclasses.asdict(self.config).items():
                    if k in dataclasses.asdict(self._manifest):
                        self.set_field(k, v)

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

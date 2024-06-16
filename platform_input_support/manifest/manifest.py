import sys
from datetime import datetime
from functools import wraps
from importlib import import_module

from loguru import logger

from platform_input_support.manifest.models import ManifestReport, Status, StepReport, TaskReport


class ManifestReporter:
    def __init__(self):
        self._report = ManifestReport()

    def start_manifest(self):
        self._report.modified = datetime.now()
        self._report.status = Status.NOT_COMPLETED

    def complete_manifest(self):
        self._report.status = Status.COMPLETED

    def fail_manifest(self, error: Exception):
        self._report.log.append(str(error))
        self._report.status = Status.FAILED

    def pass_validation_manifest(self):
        self._report.status = Status.VALIDATION_PASSED

    def fail_validation_manifest(self, error: Exception):
        self._report.log.append(str(error))
        self._report.status = Status.VALIDATION_FAILED

    def add_step(self, step: StepReport):
        self._report.steps[step.name] = step


class StepReporter:
    def __init__(self, name: str):
        self.name = name
        self._report = StepReport(self.name)

    def start_step(self):
        logger.info('starting step')
        self._report.status = Status.NOT_COMPLETED

    def complete_step(self):
        logger.success('step completed')
        self._report.status = Status.COMPLETED

    def fail_step(self, error: Exception):
        logger.error(f'failed step: f{error}')
        self._report.log.append(str(error))
        self._report.status = Status.FAILED

    def pass_validation_step(self):
        logger.success(f'validation passed {self._report.name}')
        self._report.status = Status.VALIDATION_PASSED

    def fail_validation_step(self, error: Exception):
        logger.error(f'failed validation: f{error}')
        self._report.log.append(str(error))
        self._report.status = Status.VALIDATION_FAILED

    def add_task(self, task: TaskReport):
        self._report.tasks.append(task)


class TaskReporter:
    def __init__(self, name: str):
        self.name = name
        task_class = self.__class__.__name__
        task_module = import_module(self.__module__)
        report_class = f'{task_class}Report'
        report: TaskReport = getattr(task_module, report_class, TaskReport)(name)  # TODO: get full name here!
        self._report = report

    def start_task(self):
        logger.info('starting task')
        self._report.status = Status.NOT_COMPLETED

    def complete_task(self, log: str):
        logger.success(f'task completed: {log}')
        self._report.log.append(log)
        self._report.status = Status.COMPLETED

    def fail_task(self, error: Exception):
        logger.opt(exception=sys.exc_info()).error(f'task failed: {error}')
        self._report.log.append(str(error))
        self._report.status = Status.FAILED

    def pass_validation_task(self, log: str):
        logger.success('validation passed')
        self._report.log.append(log)
        self._report.status = Status.VALIDATION_PASSED

    def fail_validation_task(self, error: Exception):
        logger.error(f'failed validation: f{error}')
        self._report.log.append(str(error))
        self._report.status = Status.VALIDATION_FAILED

    def append_log(self, log: str):
        logger.info(log)
        self._report.log.append(log)

    def set_field(self, field_name: str, value: str):
        setattr(self._report, field_name, value)


def report_to_manifest(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            if func.__name__ == 'run':
                self.start_task()

            result = func(self, *args, **kwargs)

            if func.__name__ == 'run':
                self.complete_task(result)
            elif func.__name__ == 'validate':
                self.pass_validation_task(result)
            return result
        except Exception as e:
            if func.__name__ == 'run':
                self.fail_task(e)
            elif func.__name__ == 'validate':
                self.fail_validation_task(e)

    return wrapper

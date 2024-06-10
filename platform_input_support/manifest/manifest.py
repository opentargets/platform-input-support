from datetime import datetime
from functools import wraps
from importlib import import_module

from loguru import logger

from platform_input_support.manifest.models import ActionReport, ManifestReport, Status, StepReport


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
    def __init__(self):
        self._report = StepReport()

    def start_step(self):
        step_name = self.__class__.__name__.lower()
        self._report = StepReport(name=step_name)

    def complete_step(self):
        self._report.status = Status.COMPLETED

    def fail_step(self, error: Exception):
        self._report.log.append(str(error))
        self._report.status = Status.FAILED

    def pass_validation_step(self):
        self._report.status = Status.VALIDATION_PASSED

    def fail_validation_step(self, error: Exception):
        self._report.log.append(str(error))
        self._report.status = Status.VALIDATION_FAILED

    def add_action(self, action: ActionReport):
        self._report.actions.append(action)


class ActionReporter:
    def __init__(self):
        action_class = self.__class__.__name__
        action_module = import_module(self.__module__)
        report_class = f'{action_class}Report'
        report: ActionReport = getattr(action_module, report_class, ActionReport)()
        self._report = report

    def start_action(self):
        logger.info('starting action')  # TODO: add action name
        self._report.name = self.__class__.__name__.lower()
        self._report.status = Status.NOT_COMPLETED

    def complete_action(self, log: str):
        logger.info(f'completed action {self._report.name}')
        self._report.log.append(log)
        self._report.status = Status.COMPLETED

    def fail_action(self, error: Exception):
        logger.error(str(error))
        self._report.log.append(str(error))
        self._report.status = Status.FAILED

    def pass_validation_action(self, log: str):
        logger.info(f'validation passed for action {self._report.name}')
        self._report.log.append(log)
        self._report.status = Status.VALIDATION_PASSED

    def fail_validation_action(self, error: Exception):
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
                self.start_action()

            result = func(self, *args, **kwargs)

            if func.__name__ == 'run':
                self.complete_action(result)
            elif func.__name__ == 'validate':
                self.pass_validation_action(result)
            return result
        except Exception as e:
            if func.__name__ == 'run':
                self.fail_action(e)
            elif func.__name__ == 'validate':
                self.fail_validation_action(e)
            raise

    return wrapper

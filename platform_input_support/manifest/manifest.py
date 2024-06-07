from datetime import datetime
from importlib import import_module

from platform_input_support.manifest.models import ActionReport, ManifestReport, Status, StepReport


class ManifestReporter:
    def __init__(self):
        self._report = ManifestReport()

    def start_manifest(self):
        self._report.modified = datetime.now()
        self._report.status = Status.NOT_COMPLETED

    def complete_manifest(self):
        self._report.status = Status.COMPLETED

    def fail_manifest(self, msg: str | None):
        if msg:
            self._report.log.append(msg)

        self._report.status = Status.FAILED

    def pass_validation_manifest(self):
        self._report.status = Status.VALIDATION_PASSED

    def fail_validation_manifest(self, msg: str | None):
        if msg:
            self._report.log.append(msg)

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

    def fail_step(self, msg: str | None):
        if msg:
            self._report.log.append(msg)

        self._report.status = Status.FAILED

    def pass_validation_step(self):
        self._report.status = Status.VALIDATION_PASSED

    def fail_validation_step(self, msg: str | None):
        if msg:
            self._report.log.append(msg)

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
        self._report.name = self.__class__.__name__.lower()
        self._report.status = Status.NOT_COMPLETED

    def complete_action(self):
        self._report.status = Status.COMPLETED

    def fail_action(self, msg: str | None):
        if msg:
            self._report.log.append(msg)

        self._report.status = Status.FAILED

    def pass_validation_action(self):
        self._report.status = Status.VALIDATION_PASSED

    def fail_validation_action(self, msg: str | None):
        if msg:
            self._report.log.append(msg)

        self._report.status = Status.VALIDATION_FAILED

    def set_field(self, field_name: str, value: str):
        setattr(self._report, field_name, value)

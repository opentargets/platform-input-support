from datetime import datetime

from platform_input_support.manifest.models import ActionReport, ManifestReport, ResourceReport, Status, StepReport


class ManifestReporter:
    def __init__(self):
        self._manifest = ManifestReport()

    def start_manifest(self):
        self._manifest.modified = datetime.now()
        self._manifest.status = Status.NOT_COMPLETED

    def complete_manifest(self):
        self._manifest.status = Status.COMPLETED

    def fail_manifest(self, msg: str | None):
        if msg:
            self._manifest.log.append(msg)

        self._manifest.status = Status.FAILED

    def pass_validation_manifest(self):
        self._manifest.status = Status.VALIDATION_PASSED

    def fail_validation_manifest(self, msg: str | None):
        if msg:
            self._manifest.log.append(msg)

        self._manifest.status = Status.VALIDATION_FAILED

    def add_step(self, step: StepReport):
        self._manifest.steps[step.name] = step


class StepReporter:
    def __init__(self):
        self._step = StepReport()

    def start_step(self):
        step_name = self.__class__.__name__.lower()
        self._step = StepReport(name=step_name)

    def complete_step(self):
        self._step.status = Status.COMPLETED

    def fail_step(self, msg: str | None):
        if msg:
            self._step.log.append(msg)

        self._step.status = Status.FAILED

    def pass_validation_step(self):
        self._step.status = Status.VALIDATION_PASSED

    def fail_validation_step(self, msg: str | None):
        if msg:
            self._step.log.append(msg)

        self._step.status = Status.VALIDATION_FAILED

    def add_action(self, action: ActionReport):
        self._step.actions.append(action)


class ActionReporter:
    def __init__(self):
        self._action = ActionReport()

    def start_action(self):
        self._action.name = self.__class__.__name__.lower()
        self._action.status = Status.NOT_COMPLETED

    def complete_action(self):
        self._action.status = Status.COMPLETED

    def fail_action(self, msg: str | None):
        if msg:
            self._action.log.append(msg)

        self._action.status = Status.FAILED

    def pass_validation_action(self):
        self._action.status = Status.VALIDATION_PASSED

    def fail_validation_action(self, msg: str | None):
        if msg:
            self._action.log.append(msg)

        self._action.status = Status.VALIDATION_FAILED

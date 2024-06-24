from threading import Event

from loguru import logger

from platform_input_support.manifest.models import Status, StepManifest, TaskManifest
from platform_input_support.manifest.util import recount


class StepReporter:
    def __init__(self, name: str):
        self.name = name
        self._manifest = StepManifest(name=self.name)

    def add_task_report(self, task_manifest: TaskManifest, abort: Event):
        self._manifest.tasks.append(task_manifest)
        if task_manifest.status not in [Status.COMPLETED, Status.VALIDATION_PASSED]:
            abort.set()

    def complete(self):
        self._manifest.status = Status.COMPLETED
        recount(self._manifest.tasks, self._manifest)

    def fail(self, reason: str, error: Exception | None = None):
        self._manifest.status = Status.FAILED
        msg = f'step {self.name} failed: {reason}'
        self._manifest.log.append(msg)
        logger.critical(msg)
        if error:
            self._manifest.log.append(str(error))

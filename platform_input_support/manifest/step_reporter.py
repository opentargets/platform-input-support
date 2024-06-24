from threading import Event

from loguru import logger

from platform_input_support.manifest.models import Status, StepManifest, TaskManifest


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

        total = len(self._manifest.tasks)
        success = 0
        failed = 0
        aborted = 0

        for task in self._manifest.tasks:
            self._manifest.log.append(f'task {task.name} {task.status.value}')

            if task.status == Status.NOT_COMPLETED:
                self._manifest.status = Status.FAILED
                logger.error(f'task {task.name} was interrupted for an unknown reason')
            if task.status == Status.ABORTED:
                self._manifest.status = Status.FAILED
                aborted += 1
            elif task.status == Status.FAILED:
                self._manifest.status = Status.FAILED
                failed += 1
            else:
                success += 1

        failed_summary = f', {failed}/{total} tasks failed' if failed else ''
        aborted_summary = f', {aborted}/{total} tasks aborted' if aborted else ''
        self._manifest.log.append(f'step summary: {success}/{total} tasks succeeded{failed_summary}{aborted_summary}')

    def fail(self, reason: str, error: Exception | None = None):
        self._manifest.status = Status.FAILED
        msg = f'step {self.name} failed: {reason}'
        self._manifest.log.append(msg)
        logger.critical(msg)
        if error:
            self._manifest.log.append(str(error))

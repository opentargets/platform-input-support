from platform_input_support.manifest.models import Status, StepManifest, TaskManifest


class StepReporter:
    def __init__(self, name: str):
        self.name = name
        self._manifest = StepManifest(name=self.name)

    def complete(self, task_manifests: list[TaskManifest]):
        self._manifest.tasks = task_manifests
        self._manifest.status = Status.COMPLETED
        for task in self._manifest.tasks:
            if task.status not in [Status.COMPLETED, Status.VALIDATION_PASSED]:
                self._manifest.status = Status.FAILED
                self._manifest.log.append(f'task `{task.name}` failed')

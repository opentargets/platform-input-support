from platform_input_support.manifest.models import Status, StepManifest, TaskManifest


class StepReporter:
    def __init__(self, name: str):
        self.name = name
        self._manifest = StepManifest(name=self.name)

    def add_task_reports(self, task_manifests: list[TaskManifest] | TaskManifest):
        self._manifest.tasks.extend(task_manifests if isinstance(task_manifests, list) else [task_manifests])

    def complete(self):
        self._manifest.status = Status.COMPLETED
        for task in self._manifest.tasks:
            if task.status not in [Status.COMPLETED, Status.VALIDATION_PASSED]:
                self._manifest.status = Status.FAILED
                self._manifest.log.append(f'task `{task.name}` failed')

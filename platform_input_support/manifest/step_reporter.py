from importlib import import_module

from loguru import logger

from platform_input_support.manifest.models import Status, StepManifest, TaskManifest
from platform_input_support.task.task import Task


class StepReporter:
    def __init__(self, name: str, *, manifest: StepManifest):
        self.name = name
        self._manifest = manifest

    def start(self):
        logger.info(f'starting step {self.name}')
        self._manifest.status = Status.NOT_COMPLETED

    def end(self, task_result_manifests: list[TaskManifest]):
        for task in task_result_manifests:
            # delete previous instances of this task
            for previous_task in self._manifest.tasks:
                if task.name == previous_task.name:
                    self._manifest.tasks.remove(previous_task)
                    break
            self._manifest.tasks.append(task)

        self._manifest.status = Status.COMPLETED
        for task in self._manifest.tasks:
            if task.status is not Status.COMPLETED:
                self._manifest.status = Status.FAILED
                self._manifest.log.append(f'task {task.name} failed')

    def validate(self):
        self._manifest.status = Status.VALIDATION_PASSED
        for task in self._manifest.tasks:
            if task.status is not Status.VALIDATION_PASSED:
                self._manifest.status = Status.VALIDATION_FAILED
                self._manifest.log.append(f'task {task.name} failed validation')

    def get_task_manifest(self, task: Task) -> TaskManifest:
        task_manifest = next((t for t in self._manifest.tasks if t.name == task.name), None)
        if task_manifest is not None:
            logger.debug(f'found existing manifest for task `{task.name}` with status `{task_manifest.status}`')
            return task_manifest

        # no previous manifest found, instantiate a new one of the proper type
        task_module = import_module(task.__module__)
        manifest = getattr(task_module, f'{task.__class__.__name__}Manifest', TaskManifest)(name=self.name)
        logger.debug(f'no previous manifest found for task {self.name}, created a new one')
        return manifest

    def must_run(self) -> bool:
        return self._manifest.status not in [Status.COMPLETED, Status.VALIDATION_PASSED]

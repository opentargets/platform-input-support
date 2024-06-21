from multiprocessing.pool import Pool
from typing import TYPE_CHECKING

from loguru import logger

from platform_input_support.config import task_definitions
from platform_input_support.manifest.step_reporter import StepReporter
from platform_input_support.task import task_registry
from platform_input_support.util.logger import task_logging

if TYPE_CHECKING:
    from platform_input_support.config.models import TaskDefinition
    from platform_input_support.manifest.models import TaskManifest
    from platform_input_support.task import Task

PARALLEL_STEP_COUNT = 5


class Step(StepReporter):
    def __init__(self, name: str):
        super().__init__(name)

    def _get_pre_tasks(self) -> list['TaskDefinition']:
        return [task_definitions.pop(i) for i, t in enumerate(task_definitions) if task_registry.is_pre(t)]

    def _run_task(self, task: 'Task') -> 'TaskManifest':
        with task_logging(task):
            task.run()
        return task._manifest

    def run(self):
        # run preprocess tasks
        logger.info('running pre tasks')
        for td in self._get_pre_tasks():
            if task_registry.is_pre(td):
                t = task_registry.instantiate(td)
                task_result_manifest = self._run_task(t)
                self.add_task_reports(task_result_manifest)

        # run main tasks
        tasks_to_run: list[Task] = []
        for td in task_definitions:
            t = task_registry.instantiate(td)
            tasks_to_run.append(t)

        logger.info(f'running {len(tasks_to_run)} main tasks')
        pool = Pool(PARALLEL_STEP_COUNT)
        task_result_manifests = pool.map(self._run_task, tasks_to_run)

        self.add_task_reports(task_result_manifests)
        self.complete()

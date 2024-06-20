from multiprocessing.pool import Pool
from typing import TYPE_CHECKING

from loguru import logger

from platform_input_support.config import task_definitions
from platform_input_support.manifest.step_reporter import StepReporter
from platform_input_support.task import PREPROCESS_TASKS, task_registry
from platform_input_support.util.misc import real_name

if TYPE_CHECKING:
    from platform_input_support.config.models import TaskDefinition
    from platform_input_support.manifest.models import TaskManifest
    from platform_input_support.task import Task

PARALLEL_STEP_COUNT = 5


class Step(StepReporter):
    def __init__(self, name: str):
        super().__init__(name)
        self.main_task_definitions: list[TaskDefinition] = []
        self.preprocess_task_definitions: list[TaskDefinition] = []

        for t in task_definitions:
            if real_name(t) in PREPROCESS_TASKS:
                self.preprocess_task_definitions.append(t)
            else:
                self.main_task_definitions.append(t)

    def _run_task(self, task: 'Task') -> 'TaskManifest':
        with logger.contextualize(task=task.name):
            task.run()
        return task._manifest

    def run(self):
        logger.info(f'running {len(self.preprocess_task_definitions)} preprocess tasks')
        for td in self.preprocess_task_definitions:
            t = task_registry.instantiate(td)
            self._run_task(t)

        tasks_to_run: list[Task] = []
        for td in self.main_task_definitions:
            t = task_registry.instantiate(td)
            tasks_to_run.append(t)

        logger.info(f'running {len(tasks_to_run)} main tasks')
        pool = Pool(PARALLEL_STEP_COUNT)
        task_result_manifests = pool.map(self._run_task, tasks_to_run)

        self.complete(task_result_manifests)

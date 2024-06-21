from multiprocessing.pool import Pool
from typing import TYPE_CHECKING

from loguru import logger

from platform_input_support.config import settings, task_definitions
from platform_input_support.manifest.step_reporter import StepReporter
from platform_input_support.task import PREPROCESS_TASKS, task_registry
from platform_input_support.util.logger import format_task_log
from platform_input_support.util.misc import real_name

if TYPE_CHECKING:
    from platform_input_support.config.models import TaskDefinition
    from platform_input_support.manifest.models import TaskManifest
    from platform_input_support.task import Task

PARALLEL_STEP_COUNT = 5


class Step(StepReporter):
    def __init__(self, name: str):
        super().__init__(name)

    def _split_tasks(self) -> list['TaskDefinition']:
        return [task_definitions.pop(i) for i, t in enumerate(task_definitions) if real_name(t) in PREPROCESS_TASKS]

    def _run_task(self, task: 'Task') -> 'TaskManifest':
        def sink_task(message):
            task._manifest.log.append(message)

        with logger.contextualize(task=task.name):
            logger.add(
                sink_task,
                filter=lambda record: record['extra'].get('task') == task.name,
                format=format_task_log,
                level=settings.log_level,
            )

            task.run()
        return task._manifest

    def run(self):
        # run preprocess tasks
        tds = self._split_tasks()
        logger.info(f'running {len(tds)} preprocess tasks')
        for td in tds:
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

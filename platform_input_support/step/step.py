from multiprocessing.pool import Pool

from loguru import logger

from platform_input_support.config.models import TaskMapping
from platform_input_support.manifest.models import StepManifest, TaskManifest
from platform_input_support.manifest.step_reporter import StepReporter
from platform_input_support.task import PREPROCESS_TASKS, Task, task_repository

PARALLEL_STEP_COUNT = 5


class Step(StepReporter):
    def __init__(
        self,
        name: str,
        *,
        task_mappings: list[TaskMapping],
        manifest: StepManifest,
    ):
        super().__init__(name, manifest=manifest)
        self.main_task_mappings: list[TaskMapping] = []
        self.preprocess_task_mappings: list[TaskMapping] = []

        for t in task_mappings:
            if t.real_name() in PREPROCESS_TASKS:
                self.preprocess_task_mappings.append(t)
            else:
                self.main_task_mappings.append(t)

    def _run_task(self, task: Task) -> TaskManifest:
        with logger.contextualize(task=task.name):
            task.run()
        return task._manifest

    def run(self):
        if not self.must_run():
            logger.info(f'step {self.name} already completed, and no force flag set, skipping')
            return

        self.start()

        logger.info(f'running {len(self.preprocess_task_mappings)} preprocess tasks')
        for tm in self.preprocess_task_mappings:
            t = task_repository.instantiate(tm)
            self._run_task(t)

        tasks_to_run: list[Task] = []
        for tm in self.main_task_mappings:
            t = task_repository.instantiate(tm)
            t.attach_manifest(self.get_task_manifest(t))
            if t.must_run():
                tasks_to_run.append(t)
            else:
                logger.info(f'task {t.name} already completed, skipping')

        logger.info(f'running {len(tasks_to_run)} main tasks')
        pool = Pool(PARALLEL_STEP_COUNT)
        task_result_manifests = pool.map(self._run_task, tasks_to_run)
        self.end(task_result_manifests)

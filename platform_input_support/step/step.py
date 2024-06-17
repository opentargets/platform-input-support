from multiprocessing.pool import Pool

from loguru import logger

from platform_input_support.config.models import TaskMapping
from platform_input_support.manifest import Manifest
from platform_input_support.manifest.reporters import StepReporter
from platform_input_support.task.task_repository import PREPROCESS_TASKS, task_repository

PARALLEL_STEP_COUNT = 5


class Step(StepReporter):
    def __init__(self, name: str, tasks: list[TaskMapping]):
        super().__init__(name)
        self.tasks = tasks

    def _get_preprocess_tasks(self) -> list[TaskMapping]:
        return [self.tasks.pop(i) for i, j in enumerate(self.tasks) if j.real_name() in PREPROCESS_TASKS]

    def _run_task(self, config: TaskMapping):
        task = task_repository.instantiate(config)
        self.add_task(task)

        with logger.contextualize(task=task.name):
            try:
                task.run()
            except Exception as e:
                self.fail(e)

    def run(self):
        m = Manifest()
        self.start()

        preprocess_tasks = self._get_preprocess_tasks()
        if preprocess_tasks:
            logger.info(f'running {len(preprocess_tasks)} preprocess tasks')
            for am in preprocess_tasks:
                self._run_task(am)

        logger.info(f'running {len(self.tasks)} main tasks')
        pool = Pool(PARALLEL_STEP_COUNT)
        pool.map(self._run_task, self.tasks)

        self.complete()
        m.add_step(self)
        m.close()

        print('MANIFESTn\n', m._manifest)

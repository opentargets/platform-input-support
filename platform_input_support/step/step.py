from multiprocessing.pool import Pool

from loguru import logger

from platform_input_support.config.models import TaskMapping
from platform_input_support.manifest.manifest import StepReporter
from platform_input_support.task import task_repository

PARALLEL_STEP_COUNT = 5
PREPROCESS_TASKS = ['explode', 'get_file_list']


class Step(StepReporter):
    def __init__(self, name: str, tasks: list[TaskMapping]):
        self.name: str = name
        self.tasks = tasks
        super().__init__(name)

    def _get_preprocess_tasks(self) -> list[TaskMapping]:
        return [self.tasks.pop(i) for i, j in enumerate(self.tasks) if j.real_name() in PREPROCESS_TASKS]

    def _run_task(self, am: TaskMapping):
        task_type = task_repository.tasks[am.real_name()]
        task = task_type(am.config)
        task.name = am.name

        with logger.contextualize(task=task.name):
            try:
                task.run()
            except Exception as e:
                self.fail_step(e)

    def run(self):
        self.start_step()

        preprocess_tasks = self._get_preprocess_tasks()
        logger.info(f'running {len(preprocess_tasks)} preprocess tasks')
        for am in preprocess_tasks:
            self._run_task(am)

        logger.info(f'running {len(self.tasks)} main tasks')
        pool = Pool(PARALLEL_STEP_COUNT)
        pool.map(self._run_task, self.tasks)

        self.complete_step()

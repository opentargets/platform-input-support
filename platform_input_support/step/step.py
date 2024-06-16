import sys
from importlib import import_module
from multiprocessing.pool import Pool

from loguru import logger

from platform_input_support.config.models import TaskMapping
from platform_input_support.manifest.manifest import StepReporter
from platform_input_support.task import task_repository

PARALLEL_STEP_COUNT = 5
PREPROCESS_TASKS = ['explode', 'get_file_list']


class Step(StepReporter):
    def __init__(self, name: str, tasks: list[TaskMapping]):
        super().__init__(name)
        self.tasks = tasks

    def _get_preprocess_tasks(self) -> list[TaskMapping]:
        return [self.tasks.pop(i) for i, j in enumerate(self.tasks) if j.real_name() in PREPROCESS_TASKS]

    def _run_task(self, am: TaskMapping):
        # get task class from the repository
        try:
            task_class = task_repository.tasks[am.real_name()]
        except KeyError:
            logger.critical(f'invalid task name: {am.real_name()}')
            sys.exit(1)

        # import task module and get config class
        task_module = import_module(task_class.__module__)
        config_class_name = f'{task_class.__name__}Mapping'
        try:
            config_class: type[TaskMapping] = getattr(task_module, config_class_name)
        except AttributeError:
            logger.critical(f'{task_class.__name__} task is invalid, {config_class_name}ConfigMapping class not found')
            sys.exit(1)

        # create config and task instances
        try:
            config = config_class(**am.config_dict, config_dict=am.config_dict)
        except TypeError as e:
            logger.critical(f'invalid config for {task_class}: {e}')
            sys.exit(1)
        task = task_class(config)

        # run the task
        with logger.contextualize(task=task.name):
            try:
                task.run()
            except Exception as e:
                self.fail(e)

    def run(self):
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

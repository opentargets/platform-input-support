from collections.abc import Callable
from multiprocessing import Manager
from multiprocessing.pool import Pool
from threading import Event
from typing import TYPE_CHECKING

from loguru import logger

from platform_input_support.config import task_definitions
from platform_input_support.manifest.step_reporter import StepReporter, report
from platform_input_support.task import task_registry
from platform_input_support.util.errors import StepFailedError
from platform_input_support.util.logger import task_logging

if TYPE_CHECKING:
    from platform_input_support.task import Pretask, Task

PARALLEL_STEP_COUNT = 5


def _executor(task: 'Task', func_name: str, abort: Event) -> 'Task':
    with task_logging(task):
        if not abort.is_set():
            func: Callable = getattr(task, func_name)
            func(abort=abort)
        else:
            task.aborted()
        return task


def _execute(args):
    task, func_name, abort = args
    return _executor(task, func_name, abort)


class XPool(Pool):
    def xmap(self, func_name: str, tasks: list['Task'], abort: Event) -> list['Task']:
        return list(self.imap_unordered(_execute, [(t, func_name, abort) for t in tasks]))


class Step(StepReporter):
    def __init__(self, name: str):
        super().__init__(name)

    def _instantiate_pretasks(self) -> list['Pretask']:
        logger.debug('instantiating pretasks')
        return [task_registry().instantiate_p(td) for td in task_definitions() if task_registry().is_pretask(td)]

    def _instantiate_tasks(self) -> list['Task']:
        logger.debug('instantiating tasks')
        return [task_registry().instantiate_t(td) for td in task_definitions() if not task_registry().is_pretask(td)]

    @report
    def _init(self, pretasks: list['Pretask'], *, abort: Event) -> list['Task']:
        logger.info(f'running {len(pretasks)} pretasks' if len(pretasks) > 0 else 'no pretasks to run in this step')
        return [_executor(p, 'run', abort) for p in pretasks]

    @report
    def _run(self, tasks: list['Task'], *, abort: Event) -> list['Task']:
        logger.info(f'running {len(task_definitions())} main tasks')
        with XPool(PARALLEL_STEP_COUNT) as run_pool:
            return run_pool.xmap('run', tasks, abort)

    @report
    def _validate(self, tasks: list['Task'], *, abort: Event) -> list['Task']:
        logger.info(f'validating {len(task_definitions())} main tasks')
        with XPool(PARALLEL_STEP_COUNT) as validation_pool:
            return validation_pool.xmap('validate', tasks, abort)

    @report
    def _upload(self, tasks: list['Task'], *, abort: Event) -> list['Task']:
        logger.info(f'uploading {len(task_definitions())} main tasks')
        with XPool(PARALLEL_STEP_COUNT) as upload_pool:
            return upload_pool.xmap('upload', tasks, abort)

    def execute(self):
        with Manager() as manager:
            a = manager.Event()

            try:
                # pretask process, sequential execution of initialization tasks
                pretasks = self._instantiate_pretasks()

                pretasks = self._init(pretasks, abort=a)
                if a.is_set():
                    raise StepFailedError(self.name, 'initialization')

                # main process, parallel execution of resource generating tasks
                tasks = self._instantiate_tasks()

                tasks = self._run(tasks, abort=a)
                if a.is_set():
                    raise StepFailedError(self.name, 'run')

                tasks = self._validate(tasks, abort=a)
                if a.is_set():
                    raise StepFailedError(self.name, 'validation')

                tasks = self._upload(tasks, abort=a)
                if a.is_set():
                    raise StepFailedError(self.name, 'upload')
            except Exception as e:
                a.set()
                self.failed(f'step execution failed: {e}')
            return self

"""Step module."""

from collections.abc import Callable
from multiprocessing import Manager
from multiprocessing.pool import Pool
from threading import Event
from typing import TYPE_CHECKING

from loguru import logger

from pis.config import settings, task_definitions
from pis.manifest.step_reporter import StepReporter, report
from pis.task import task_registry
from pis.util.errors import StepFailedError
from pis.util.logger import task_logging

if TYPE_CHECKING:
    from pis.task import Pretask, Task


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
    """Extended Pool class.

    This class extends the Pool class to add an xmap method that allows for the execution of
    a function on a list of tasks, while also providing an abort mechanism.
    """

    def xmap(self, func_name: str, tasks: list['Task'], abort: Event) -> list['Task']:
        """Execute a function on a list of tasks.

        This is a wrapper for imap_unordered that allows for the execution of a function
        on a list of tasks with arbitrary parameters without having to clump them together
        in a single tuple. It also provides an abort mechanism.

        :param func_name: The name of the function to execute on the tasks.
        :type func_name: str
        :param tasks: The list of tasks to execute the function on.
        :type tasks: list[Task]
        :param abort: The abort event to signal the tasks to stop execution.
        :type abort: Event

        :return: The list of tasks after the function has been executed on them.
        :rtype: list[Task]
        """
        return list(self.imap_unordered(_execute, [(t, func_name, abort) for t in tasks]))


class Step(StepReporter):
    """Step class.

    This class represents a step in the pipeline. A step is a collection of pretasks and
    tasks. The step will:

    1. Initialize the pretasks.
    2. Run the pretasks.
    3. Initialize the tasks.
    4. Send the tasks to the pool for parallel execution.
    5. Validate the tasks.
    6. Upload the tasks.

    :ivar name: The name of the step.
    :vartype name: str
    """

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
        with XPool(settings().pool) as run_pool:
            return run_pool.xmap('run', tasks, abort)

    @report
    def _validate(self, tasks: list['Task'], *, abort: Event) -> list['Task']:
        logger.info(f'validating {len(task_definitions())} main tasks')
        with XPool(settings().pool) as validation_pool:
            return validation_pool.xmap('validate', tasks, abort)

    @report
    def _upload(self, tasks: list['Task'], *, abort: Event) -> list['Task']:
        logger.info(f'uploading {len(task_definitions())} main tasks')
        with XPool(settings().pool) as upload_pool:
            return upload_pool.xmap('upload', tasks, abort)

    def execute(self):
        """Execute the step.

        :raises StepFailedError: If the step execution fails at any point.
        :return: The step instance itself.
        :rtype: Step
        """
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

                if settings().remote_uri:
                    tasks = self._upload(tasks, abort=a)
                    if a.is_set():
                        raise StepFailedError(self.name, 'upload')
                else:
                    logger.info('no remote URI provided, skipping upload phase')
            except Exception as e:
                a.set()
                self.failed(f'step execution failed: {e}')
            return self

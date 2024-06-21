from multiprocessing import Manager
from multiprocessing.pool import Pool
from threading import Event
from typing import TYPE_CHECKING

from loguru import logger

from platform_input_support.config import task_definitions
from platform_input_support.manifest.step_reporter import StepReporter
from platform_input_support.task import task_registry
from platform_input_support.util.errors import ScratchpadError, TaskAbortedError
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

    def _run_task_wrap(self, args):
        return self._run_task(*args)

    def _run_task(self, task: 'Task', abort: Event) -> 'TaskManifest':
        with task_logging(task):
            if abort.is_set():
                task.fail(TaskAbortedError())
            else:
                try:
                    task.run(abort)
                except Exception as e:
                    task.fail(e)
            return task._manifest

    def run(self):
        with Manager() as manager:
            abort = manager.Event()

            # run preprocess tasks
            logger.info('running pretasks')
            for td in self._get_pre_tasks():
                t = task_registry.instantiate(td)
                self.add_task_report(self._run_task(t, abort), abort)

            # make sure all pretasks passed
            if abort.is_set():
                self.fail('some pretasks failed')
                return

            # instantiate the main tasks that have to be run
            tasks_to_run: list[Task] = []
            for td in task_definitions:
                try:
                    t = task_registry.instantiate(td)
                except ScratchpadError as e:
                    self.fail('some tasks failed to initialize', e)
                    return
                tasks_to_run.append(t)

            # send tasks to a parallel pool
            logger.info(f'running {len(tasks_to_run)} main tasks')
            with Pool(PARALLEL_STEP_COUNT) as pool:
                task_result_manifests = pool.imap_unordered(self._run_task_wrap, [(t, abort) for t in tasks_to_run])
                # periodically checks for completion and aborts if necessary
                for m in task_result_manifests:
                    self.add_task_report(m, abort)

            # complete the step
            self.complete()

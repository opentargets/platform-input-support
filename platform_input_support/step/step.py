from multiprocessing import Manager
from multiprocessing.pool import Pool
from threading import Event
from typing import TYPE_CHECKING, cast

from loguru import logger

from platform_input_support.config import task_definitions
from platform_input_support.config.models import PretaskDefinition
from platform_input_support.manifest.step_reporter import StepReporter
from platform_input_support.task import task_registry
from platform_input_support.util.errors import StepFailedError, TaskAbortedError
from platform_input_support.util.logger import task_logging

if TYPE_CHECKING:
    from platform_input_support.task import Task

PARALLEL_STEP_COUNT = 5


class Step(StepReporter):
    def __init__(self, name: str):
        super().__init__(name)
        self.main_tasks: list[Task] = []

    def _get_pretasks(self) -> list['PretaskDefinition']:
        return [
            cast(PretaskDefinition, task_definitions().pop(i))
            for i, t in enumerate(task_definitions())
            if task_registry().is_pretask(t)
        ]

    def _run_task_wrap(self, args) -> 'Task':
        return self._run_task(*args)

    def _run_task(self, task: 'Task', abort_event: Event) -> 'Task':
        with task_logging(task):
            if not abort_event.is_set():
                try:
                    task.run(abort_event)
                except TaskAbortedError:
                    task.abort()
                except Exception as e:
                    abort_event.set()
                    task.fail(e)
            else:
                task.abort()
            return task

    def run(self) -> None:
        with Manager() as manager:
            abort_event = manager.Event()

            # run pretasks
            logger.info('running pretasks')
            for td in self._get_pretasks():
                try:
                    t = task_registry().instantiate(td)
                except Exception as e:
                    self.fail(f'some pretasks failed to initialize: {e}')
                    return
                self._run_task(t, abort_event)

            # instantiate the main tasks that have to be run
            for td in task_definitions():
                try:
                    t = task_registry().instantiate(td)
                except Exception as e:
                    self.fail(f'some tasks failed to initialize: {e}')
                    return
                self.main_tasks.append(t)

            # send tasks to a parallel pool
            logger.info(f'running {len(self.main_tasks)} main tasks')
            updated_tasks = []
            with Pool(PARALLEL_STEP_COUNT) as run_pool:
                results = run_pool.imap_unordered(
                    self._run_task_wrap,
                    [(t, abort_event) for t in self.main_tasks],
                )
                # add task with the report filled to the list of updated tasks
                updated_tasks.extend(list(results).copy())

            # fail the step if any task failed
            if abort_event.is_set():
                self.abort()
                raise StepFailedError(self.name)
            else:
                self.stage('all tasks have been run')
                self.main_tasks = updated_tasks

    def _upload_file_wrap(self, args):
        return self._upload_file(*args)

    def _upload_file(self, task: 'Task', abort_event: Event) -> 'Task':
        with task_logging(task):
            if abort_event.is_set():
                task.fail(TaskAbortedError())
            else:
                try:
                    task.upload()
                except Exception as e:
                    abort_event.set()
                    task.fail(e)
            return task

    def upload(self):
        with Manager() as manager:
            abort_event = manager.Event()

            # send tasks to a parallel pool
            logger.info(f'uploading files from {len(self.main_tasks)} main tasks')
            with Pool(PARALLEL_STEP_COUNT) as upload_pool:
                results = upload_pool.imap_unordered(
                    self._upload_file_wrap,
                    [(t, abort_event) for t in self.main_tasks],
                )
                # add task reports to the step
                for t in results:
                    self.add_task(t)
                    t.complete('upload successful')

            # fail the step if any task failed
            if abort_event.is_set():
                self.fail('step aborted')
            else:
                self.complete('all tasks have been uploaded')

    def validation(self):
        print('VALIDATION STEP')

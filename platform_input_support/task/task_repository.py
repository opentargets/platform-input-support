from importlib import import_module
from inspect import getmembers, isclass
from pathlib import Path

from loguru import logger

from platform_input_support.task import Task

tasks_dir = Path(__file__).parent.parent / 'tasks'
tasks_module = 'platform_input_support.tasks'


class TaskRepository:
    def __init__(self):
        self.tasks: dict[str, type[Task]] = {}

    @staticmethod
    def _filename_to_class(filename: str) -> str:
        return filename.replace('_', ' ').title().replace(' ', '')

    def _register_task(self, task_name: str, task_class: type[Task]):
        self.tasks[task_name] = task_class
        logger.debug(f'registered task {task_name}')

    def register_tasks(self):
        logger.debug(f'registering tasks from {tasks_dir}')

        for file_path in tasks_dir.glob('*.py'):
            filename = file_path.stem
            task_module = import_module(f'{tasks_module}.{filename}')

            if task_module.__spec__ is None:
                continue

            for name, obj in getmembers(task_module):
                if isclass(obj) and name == self._filename_to_class(filename):
                    self._register_task(filename, obj)
                    break


task_repository = TaskRepository()
task_repository.register_tasks()

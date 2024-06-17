from __future__ import annotations

import sys
from importlib import import_module
from inspect import getmembers, isclass
from pathlib import Path

from loguru import logger

from platform_input_support.config.models import TaskMapping
from platform_input_support.task import Task

TASKS_DIR = Path(__file__).parent.parent / 'tasks'
TASKS_MODULE = 'platform_input_support.tasks'


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
        logger.debug(f'registering tasks from {TASKS_DIR}')

        for file_path in TASKS_DIR.glob('*.py'):
            filename = file_path.stem
            task_module = import_module(f'{TASKS_MODULE}.{filename}')

            if task_module.__spec__ is None:
                continue

            for name, obj in getmembers(task_module):
                if isclass(obj) and name == self._filename_to_class(filename):
                    self._register_task(filename, obj)
                    break

    def instantiate(self, config: TaskMapping) -> Task:
        task_class_name = config.real_name()

        # get task class from the repository
        try:
            task_class = self.tasks[task_class_name]
        except KeyError:
            logger.critical(f'invalid task name: {task_class_name}')
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
            config = config_class(**config.config_dict, config_dict=config.config_dict)
        except TypeError as e:
            logger.critical(f'invalid config for {task_class}: {e}')
            sys.exit(1)

        # instantiate and return a subclass instance
        return task_class(config)

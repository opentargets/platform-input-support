from __future__ import annotations

import sys
from importlib import import_module
from inspect import getmembers, isclass
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from platform_input_support.manifest.models import TaskManifest
from platform_input_support.util.misc import real_name

if TYPE_CHECKING:
    from platform_input_support.config.models import TaskDefinition
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
        logger.debug(f'registered task `{task_name}`')

    def register_tasks(self):
        logger.debug(f'registering tasks from `{TASKS_DIR}`')

        for file_path in TASKS_DIR.glob('*.py'):
            filename = file_path.stem
            task_module = import_module(f'{TASKS_MODULE}.{filename}')

            if task_module.__spec__ is None:
                continue

            for name, obj in getmembers(task_module):
                if isclass(obj) and name == self._filename_to_class(filename):
                    self._register_task(filename, obj)
                    break

    def instantiate(self, task_definition: TaskDefinition) -> Task:
        task_class_name = real_name(task_definition)

        # get task class from the repository
        try:
            task_class = self.tasks[task_class_name]
        except KeyError:
            logger.critical(f'invalid task name: `{task_class_name}`')
            sys.exit(1)

        # import task module and get task definition and manifest classes
        task_module = import_module(task_class.__module__)
        task_definition_class_name = f'{task_class.__name__}Definition'
        task_manifest_class_name = f'{task_class.__name__}Manifest'
        try:
            task_definition_class: type[TaskDefinition] = getattr(task_module, task_definition_class_name)
            task_manifest_class: type[TaskManifest] = getattr(task_module, task_manifest_class_name, TaskManifest)
        except AttributeError:
            logger.critical(f'`{task_class.__name__}` task missing definition or manifest classes')
            sys.exit(1)

        # create task definition and manifest instances
        try:
            definition = task_definition_class.model_validate(task_definition.model_dump())
            manifest = task_manifest_class(name=definition.name)
        except TypeError as e:
            logger.critical(f'invalid definition for `{task_class}`: {e}')
            sys.exit(1)

        # create task and attach manifest
        task = task_class(definition)
        task._manifest = manifest

        return task

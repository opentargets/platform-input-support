import importlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from pydantic import ValidationError

from platform_input_support.config.models import TaskDefinition
from platform_input_support.manifest.models import TaskManifest
from platform_input_support.task import PreTask
from platform_input_support.util.misc import real_name

if TYPE_CHECKING:
    from platform_input_support.task import Task

TASKS_DIR = Path(__file__).parent.parent / 'tasks'
TASKS_MODULE = 'platform_input_support.tasks'


class TaskRegistry:
    def __init__(self):
        self.tasks: dict[str, type[Task]] = {}
        self.task_definitions: dict[str, type[TaskDefinition]] = {}
        self.task_manifests: dict[str, type[TaskManifest]] = {}
        self.pre_tasks: list[str] = []

    @staticmethod
    def _filename_to_class(filename: str) -> str:
        return filename.replace('_', ' ').title().replace(' ', '')

    def is_pre(self, task_definition: TaskDefinition) -> bool:
        return real_name(task_definition) in self.pre_tasks

    def register_tasks(self):
        logger.debug(f'registering tasks from {TASKS_DIR}')

        for task_path in TASKS_DIR.glob('[!{_}]*.py'):
            task_name = task_path.stem
            task_module = importlib.import_module(f'{TASKS_MODULE}.{task_name}')
            task_class_name = self._filename_to_class(task_name)

            # if the task is a PreTask, add it to the list
            task_class = getattr(task_module, task_class_name)
            if issubclass(task_class.__base__, PreTask):
                self.pre_tasks.append(task_name)

            # add task and its task_definition and manifest to the registry
            self.tasks[task_name] = task_class
            self.task_definitions[task_name] = getattr(task_module, f'{task_class_name}Definition', TaskDefinition)
            self.task_manifests[task_name] = getattr(task_module, f'{task_class_name}Manifest', TaskManifest)

            logger.debug(f'registered task {task_name}')

    def instantiate(self, task_definition: TaskDefinition) -> 'Task':
        task_class_name = real_name(task_definition)

        # get task class from the registry
        try:
            task_class = self.tasks[task_class_name]
            task_definition_class = self.task_definitions[task_class_name]
            task_manifest_class = self.task_manifests[task_class_name]
        except KeyError:
            logger.critical(f'invalid task name: {task_class_name}')
            sys.exit(1)

        # create task_definition and manifest instances
        try:
            task_definition = task_definition_class.model_validate(task_definition.model_dump())
            manifest = task_manifest_class(name=task_definition.name)
        except ValidationError as e:
            logger.critical(f'invalid task_definition for {task_class}: {e}')
            sys.exit(1)

        # create task and attach manifest
        task = task_class(task_definition)
        task._manifest = manifest

        return task

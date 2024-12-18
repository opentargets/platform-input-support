"""TaskRegistry class handles the registry of tasks."""

import importlib
import sys
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from pis.config.models import BaseTaskDefinition
from pis.manifest.models import TaskManifest
from pis.task import Pretask, Task
from pis.util.misc import real_name

TASKS_DIR = Path(__file__).parent.parent / 'tasks'
TASKS_MODULE = 'pis.tasks'


class TaskRegistry:
    """TaskRegistry contains the registry of tasks.

    The registry is where PIS will instantiate tasks from when it reads the configuration
    file. It contains the mapping of task names to their respective classes, task definitions
    and manifests.

    :ivar tasks: Mapping of task names to their respective classes.
    :vartype tasks: dict[str, type[Task]]
    :ivar task_definitions: Mapping of task names to their respective task definition classes.
    :vartype task_definitions: dict[str, type[BaseTaskDefinition]]
    :ivar task_manifests: Mapping of task names to their respective task manifest classes.
    :vartype task_manifests: dict[str, type[TaskManifest]]
    :ivar pre_tasks: List of names of the pretasks.
    :vartype pre_tasks: list[str]
    """

    def __init__(self):
        self.tasks: dict[str, type[Task]] = {}
        self.task_definitions: dict[str, type[BaseTaskDefinition]] = {}
        self.task_manifests: dict[str, type[TaskManifest]] = {}
        self.pre_tasks: list[str] = []

    @staticmethod
    def _filename_to_class(filename: str) -> str:
        return filename.replace('_', ' ').title().replace(' ', '')

    def is_pretask(self, task_definition: BaseTaskDefinition) -> bool:
        """Return whether the task is a pretask.

        :param task_definition: The task definition to check.
        :type task_definition: BaseTaskDefinition
        :return: Whether the task is a pretask.
        :rtype: bool
        """
        return real_name(task_definition) in self.pre_tasks

    def register_tasks(self):
        """Register all tasks from the tasks directory."""
        logger.debug(f'registering tasks from {TASKS_DIR}')

        for task_path in TASKS_DIR.glob('[!{_}]*.py'):
            task_name = task_path.stem
            task_module = importlib.import_module(f'{TASKS_MODULE}.{task_name}')
            task_class_name = self._filename_to_class(task_name)

            # if the task is a Pretask, add it to the list
            task_class = getattr(task_module, task_class_name)
            if issubclass(task_class.__base__, Pretask):
                self.pre_tasks.append(task_name)

            # add task and its task_definition and manifest to the registry
            self.tasks[task_name] = task_class
            self.task_definitions[task_name] = getattr(task_module, f'{task_class_name}Definition', BaseTaskDefinition)
            self.task_manifests[task_name] = getattr(task_module, f'{task_class_name}Manifest', TaskManifest)

    def _instantiate(self, task_definition: BaseTaskDefinition) -> 'Task | Pretask':
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
        except ValidationError as ve:
            # log a clear message if there are missing fields, otherwise error message
            msg = ', '.join([str(e['loc'][0]) for e in ve.errors() if e['type'] == 'missing'])
            msg = f'missing fields: {msg}' if msg else ve
            logger.critical(f'invalid task_definition for task {task_class.__name__}: {msg}')
            sys.exit(1)

        # create task and attach manifest
        task = task_class(task_definition)
        task._manifest = manifest

        return task

    def instantiate_t(self, task_definition: BaseTaskDefinition) -> 'Task':
        """Instantiate a task.

        :param task_definition: The task definition to instantiate the task from.
        :type task_definition: BaseTaskDefinition
        :return: The instantiated task.
        :rtype: Task
        """
        task = self._instantiate(task_definition)
        assert isinstance(task, Task)
        return task

    def instantiate_p(self, pretask_definition: BaseTaskDefinition) -> 'Pretask':
        """Instantiate a pretask.

        :param pretask_definition: The pretask definition to instantiate the pretask from.
        :type pretask_definition: BaseTaskDefinition
        :return: The instantiated pretask.
        :rtype: Pretask
        """
        pretask = self._instantiate(pretask_definition)
        assert isinstance(pretask, Pretask)
        return pretask

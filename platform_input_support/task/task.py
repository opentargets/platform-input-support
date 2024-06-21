from threading import Event

from loguru import logger

from platform_input_support.config import scratchpad
from platform_input_support.config.models import TaskDefinition
from platform_input_support.manifest.task_reporter import TaskReporter


class Task(TaskReporter):
    def __init__(self, definition: TaskDefinition):
        super().__init__(definition.name)
        self.definition = definition

        # replace templates in the definition strings
        for key, value in vars(self.definition).items():
            if isinstance(value, str):
                setattr(self.definition, key, scratchpad.replace(value))

        logger.debug(f'initialized task `{self.name}`')

    def run(self, abort: Event) -> str | None:
        pass


class PreTask(Task):
    pass

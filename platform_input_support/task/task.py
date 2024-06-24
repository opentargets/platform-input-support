from threading import Event

from loguru import logger

from platform_input_support.config import scratchpad, settings
from platform_input_support.config.models import BaseTaskDefinition, TaskDefinition
from platform_input_support.helpers import google_helper
from platform_input_support.manifest.task_reporter import TaskReporter
from platform_input_support.util.fs import get_full_path


class Task(TaskReporter):
    def __init__(self, definition: BaseTaskDefinition):
        super().__init__(definition.name)
        self.definition = definition

        # replace templates in the definition strings
        for key, value in self.definition.model_dump().items():
            if isinstance(value, str):
                setattr(self.definition, key, scratchpad().replace(value))

        logger.debug(f'initialized task {self.name}')

    def run(self, abort_event: Event) -> str | None:
        pass

    def upload(self) -> None:
        if not isinstance(self.definition, TaskDefinition):
            logger.warning(f'attempting to upload {self.name}, which is a non-uploadable task')
            return

        source = get_full_path(self.definition.destination)
        destination = f'{settings().gcs_url}/{self.definition.destination!s}'
        google_helper().upload(source, destination)


class Pretask(Task):
    pass

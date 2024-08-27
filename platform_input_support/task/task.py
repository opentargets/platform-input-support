from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Self

from loguru import logger

from platform_input_support.config import scratchpad, settings
from platform_input_support.config.models import BaseTaskDefinition, TaskDefinition
from platform_input_support.helpers import google_helper
from platform_input_support.manifest.task_reporter import TaskReporter, report
from platform_input_support.util.errors import PISError
from platform_input_support.util.fs import absolute_path

if TYPE_CHECKING:
    from platform_input_support.manifest.models import Resource


class Task(TaskReporter):
    def __init__(self, definition: BaseTaskDefinition):
        super().__init__(definition.name)
        self.definition = definition
        self.resource: Resource

        # replace templates in the definition strings
        for key, value in self.definition.model_dump().items():
            if isinstance(value, str | Path):
                setattr(self.definition, key, scratchpad().replace(value))

        logger.debug(f'initialized task {self.name}')

    @report
    def run(self, *, abort: Event) -> Self:
        return self

    @report
    def validate(self, *, abort: Event) -> Self:
        return self

    @report
    def upload(self, *, abort: Event) -> Self:
        if not isinstance(self.definition, TaskDefinition):
            raise PISError(f'attempting to upload {self.name}, which is a non-uploadable task')

        source = absolute_path(self.definition.destination)
        destination = f'{settings().gcs_url}/{self.definition.destination!s}'

        google_helper().upload(source, destination)
        return self


class Pretask(Task):
    pass

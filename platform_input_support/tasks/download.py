from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Self

from loguru import logger

from platform_input_support.helpers.download import download
from platform_input_support.tasks import Task, TaskDefinition, report
from platform_input_support.validators import v
from platform_input_support.validators.file import file_exists, file_size


@dataclass
class DownloadDefinition(TaskDefinition):
    source: str
    destination: Path


class Download(Task):
    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: DownloadDefinition

    @report
    def run(self, *, abort: Event) -> Self:
        download(self.definition.source, self.definition.destination, abort=abort)
        logger.success('download successful')
        return self

    @report
    def validate(self, *, abort: Event) -> Self:
        v(file_exists, self.definition.destination)
        v(file_size, self.definition.source, self.definition.destination)

        return self

from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Self

from loguru import logger

from platform_input_support.helpers.download import download
from platform_input_support.manifest.models import Resource
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

    def is_google_spreadsheet(self) -> bool:
        return self.definition.source.startswith('https://docs.google.com/spreadsheets/')

    @report
    def run(self, *, abort: Event) -> Self:
        download(self.definition.source, self.definition.destination, abort=abort)
        self.resource = Resource(source=self.definition.source, destination=str(self.definition.destination))
        logger.debug('download successful')
        return self

    @report
    def validate(self, *, abort: Event) -> Self:
        v(file_exists, self.definition.destination)

        # skip size validation for google spreadsheet
        if self.is_google_spreadsheet():
            logger.warning('skipping validation for google spreadsheet')
            return self

        v(file_size, self.definition.source, self.definition.destination)

        return self

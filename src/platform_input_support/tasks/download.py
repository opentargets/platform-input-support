"""Simple download task."""

from dataclasses import dataclass
from threading import Event
from typing import Self

from loguru import logger

from platform_input_support.helpers.download import download
from platform_input_support.tasks import Resource, Task, TaskDefinition, report, v
from platform_input_support.validators.file import file_exists, file_size


@dataclass
class DownloadDefinition(TaskDefinition):
    """Configuration fields for the download task.

    This task has the following custom configuration fields:
        - source (str): The URL of the file to download.
    """

    source: str


class Download(Task):
    """Simple dowload task.

    Downloads a file from a URL to a local destination.
    """

    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: DownloadDefinition

    def _is_google_spreadsheet(self) -> bool:
        return self.definition.source.startswith('https://docs.google.com/spreadsheets/')

    @report
    def run(self, *, abort: Event) -> Self:
        """Download a file from the source URL to the destination path."""
        download(self.definition.source, self.definition.destination, abort=abort)
        self.resource = Resource(source=self.definition.source, destination=str(self.definition.destination))
        logger.debug('download successful')
        return self

    @report
    def validate(self, *, abort: Event) -> Self:
        """Check that the downloaded file exists and has a valid size."""
        v(file_exists, self.definition.destination)

        # skip size validation for google spreadsheet
        if self._is_google_spreadsheet():
            logger.warning('skipping validation for google spreadsheet')
            return self

        v(file_size, self.definition.source, self.definition.destination)

        return self

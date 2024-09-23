"""Task to download the latest file from a Google Cloud Storage bucket."""

from dataclasses import dataclass
from threading import Event
from typing import Self

from loguru import logger

from platform_input_support.helpers import google_helper
from platform_input_support.helpers.download import download
from platform_input_support.tasks import Resource, Task, TaskDefinition, report


@dataclass
class DownloadLatestDefinition(TaskDefinition):
    """Configuration fields for the download_latest task.

    This task has the following custom configuration fields:
        - source (str): The path to the Google Cloud Storage bucket to check for the latest file.
    """

    source: list[str] | str


class DownloadLatest(Task):
    """Task to download the latest file from a Google Cloud Storage bucket.

    This task list all files in a Google Cloud Storage bucket and downloads the one
    with the latest modification date.
    """

    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: DownloadLatestDefinition

    @report
    def run(self, *, abort: Event) -> Self:
        source, destination = self.definition.source, self.definition.destination

        if isinstance(source, str):
            source = google_helper().list_blobs(source)

        newest_file = google_helper().get_newest(source)
        if newest_file:
            logger.info(f'latest file is {newest_file}')
            download(newest_file, destination)
            self.resource = Resource(source=newest_file, destination=str(destination))
            logger.info('download successful')
            return self
        else:
            raise ValueError(f'no files found in {self.definition.source}')

from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Self

from loguru import logger

from platform_input_support.helpers import google_helper
from platform_input_support.helpers.download import download
from platform_input_support.manifest.models import Resource
from platform_input_support.tasks import Task, TaskDefinition, report


@dataclass
class DownloadLatestDefinition(TaskDefinition):
    source: list[str] | str
    destination: Path


class DownloadLatest(Task):
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
            logger.success('download successful')
            return self
        else:
            raise ValueError(f'no files found in {self.definition.source}')

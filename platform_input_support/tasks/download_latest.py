from dataclasses import dataclass
from pathlib import Path
from threading import Event

from loguru import logger

from platform_input_support.config.models import TaskDefinition
from platform_input_support.helpers import google_helper
from platform_input_support.helpers.download import download
from platform_input_support.manifest import report_to_manifest
from platform_input_support.task.task import Task


@dataclass
class DownloadLatestDefinition(TaskDefinition):
    source: list[str] | str
    destination: Path


class DownloadLatest(Task):
    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: DownloadLatestDefinition

    @report_to_manifest
    def run(self, abort: Event):
        source, destination = self.definition.source, self.definition.destination

        if isinstance(source, str):
            source = google_helper().list(source)

        newest_date = None
        newest_file = None

        for f in source:
            modification_date = google_helper().get_modification_date(f)
            if modification_date:
                if not newest_date or modification_date > newest_date:
                    newest_date = modification_date
                    newest_file = f

        if newest_file:
            logger.info(f'latest file is {newest_file}')
            download(newest_file, destination)
            return 'download successful'
        else:
            raise ValueError(f'no files found in {source}')

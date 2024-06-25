from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Self

from loguru import logger

from platform_input_support.helpers.download import download
from platform_input_support.tasks import Task, TaskDefinition, TaskManifest, report


@dataclass
class DownloadDefinition(TaskDefinition):
    source: str
    destination: Path


class DownloadManifest(TaskManifest):
    checksum_source: str | None = None
    checksum_destination: str | None = None


class Download(Task):
    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: DownloadDefinition

    @report
    def run(self, *, abort: Event) -> Self:
        download(self.definition.source, self.definition.destination, abort=abort)
        logger.success('download successful')
        return self

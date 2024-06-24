from dataclasses import dataclass
from pathlib import Path
from threading import Event

from pydantic import BaseModel

from platform_input_support.config.models import MainTaskDefinition, TaskDefinition
from platform_input_support.helpers.download import download
from platform_input_support.manifest import report_to_manifest
from platform_input_support.manifest.models import TaskManifest
from platform_input_support.task import Task


@dataclass
class DownloadDefinition(MainTaskDefinition):
    source: str


class DownloadManifest(TaskManifest, BaseModel):
    checksum_source: str | None = None
    checksum_destination: str | None = None


class Download(Task):
    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: DownloadDefinition

    @report_to_manifest
    def run(self, abort: Event):
        download(self.definition.source, self.definition.destination, abort=abort)
        return 'download successful'

from dataclasses import dataclass

from pydantic import BaseModel

from platform_input_support.config.models import TaskMapping
from platform_input_support.helpers.download import DownloadHelper
from platform_input_support.manifest import report_to_manifest
from platform_input_support.manifest.models import TaskManifest
from platform_input_support.task import Task


@dataclass
class DownloadMapping(TaskMapping):
    source: str
    destination: str


class DownloadManifest(TaskManifest, BaseModel):
    checksum_source: str | None = None
    checksum_destination: str | None = None


class Download(Task):
    def __init__(self, config: TaskMapping):
        super().__init__(config)
        self.config: DownloadMapping

    @report_to_manifest
    def run(self) -> str:
        d = DownloadHelper(self.config.source, self.config.destination)
        return d.download()

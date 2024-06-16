from dataclasses import dataclass

from platform_input_support.config.models import TaskMapping
from platform_input_support.helpers.download import DownloadHelper
from platform_input_support.manifest import report_to_manifest
from platform_input_support.manifest.models import Status, TaskManifest
from platform_input_support.task import Task


@dataclass
class DownloadMapping(TaskMapping):
    source: str
    destination: str


@dataclass
class DownloadManifest(TaskManifest):
    checksum_source: str | Status = Status.NOT_SET
    checksum_destination: str | Status = Status.NOT_SET


class Download(Task):
    def __init__(self, config: TaskMapping):
        self.config: DownloadMapping
        super().__init__(config)

    @report_to_manifest
    def run(self) -> str:
        d = DownloadHelper(self.config.source, self.config.destination)
        return d.download()

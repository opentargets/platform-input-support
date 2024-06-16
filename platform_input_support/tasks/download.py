from dataclasses import dataclass

from platform_input_support.helpers import DownloadHelper

from . import Status, Task, TaskManifest, TaskMapping, report_to_manifest


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
        super().__init__(config)
        self.config: DownloadMapping

    @report_to_manifest
    def run(self) -> str:
        d = DownloadHelper(self.config.source, self.config.destination)
        return d.download()

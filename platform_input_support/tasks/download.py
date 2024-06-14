from dataclasses import dataclass

from platform_input_support.helpers.download import DownloadHelper
from platform_input_support.manifest import Status, TaskReport, report_to_manifest
from platform_input_support.task import Task, TaskConfigMapping


@dataclass
class DownloadConfigMapping(TaskConfigMapping):
    source: str
    destination: str


@dataclass
class DownloadReport(TaskReport):
    checksum_source: str | Status = Status.NOT_SET
    checksum_destination: str | Status = Status.NOT_SET


class Download(Task):
    def __init__(self, config: TaskConfigMapping):
        self.config: DownloadConfigMapping
        super().__init__(config)

    @report_to_manifest
    def run(self) -> str:
        d = DownloadHelper(self.config.source, self.config.destination)
        return d.download()

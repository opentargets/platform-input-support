from dataclasses import dataclass

from platform_input_support.action import Action
from platform_input_support.action.action import ActionConfigMapping
from platform_input_support.helpers.download import DownloadHelper
from platform_input_support.manifest.manifest import report_to_manifest
from platform_input_support.manifest.models import ActionReport, Status


@dataclass
class DownloadConfigMapping(ActionConfigMapping):
    source: str
    destination: str


@dataclass
class DownloadReport(ActionReport):
    checksum_source: str | Status = Status.NOT_SET
    checksum_destination: str | Status = Status.NOT_SET


class Download(Action):
    def __init__(self, config: ActionConfigMapping):
        self.config: DownloadConfigMapping
        super().__init__(config)

    @report_to_manifest
    def run(self) -> str:
        d = DownloadHelper(self.config.source, self.config.destination)
        return d.download()

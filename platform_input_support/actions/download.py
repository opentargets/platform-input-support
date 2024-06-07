from dataclasses import dataclass
from typing import Any

from platform_input_support.action.action import Action, ActionConfigMapping
from platform_input_support.helpers.download import DownloadError, download
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
    def __init__(self, config: dict[str, Any]):
        self.config: DownloadConfigMapping
        super().__init__(config)

    def run(self):
        self.start_action()

        try:
            download(self.config.source, self.config.destination)
            self.complete_action()
        except DownloadError as e:
            self.fail_action(e)

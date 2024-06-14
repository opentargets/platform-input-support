from dataclasses import dataclass
from typing import Any

from loguru import logger

from platform_input_support.action import Action, ActionConfigMapping
from platform_input_support.helpers.download import download
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
        logger.debug(f'downloading {self.config.source} to {self.config.destination}')
        download(self.config.source, self.config.destination)
        return f'downloaded {self.config.source} to {self.config.destination}'

from dataclasses import dataclass
from typing import Any

from platform_input_support.action import Action, ActionConfigMapping
from platform_input_support.helpers.download import download
from platform_input_support.helpers.google import google
from platform_input_support.manifest.manifest import report_to_manifest


@dataclass
class DownloadLatestConfigMapping(ActionConfigMapping):
    source: list[str] | str
    destination: str


class DownloadLatest(Action):
    def __init__(self, config: dict[str, Any]):
        self.config: DownloadLatestConfigMapping
        super().__init__(config)

    @report_to_manifest
    def run(self):
        file_list = self.config.source

        if isinstance(self.config.source, str):
            file_list = google.list(self.config.source)

        newest_date = None
        newest_file = None

        for f in file_list:
            creation_date = google.get_creation_date(f)
            if creation_date:
                if not newest_date or creation_date > newest_date:
                    newest_date = creation_date
                    newest_file = f

        if newest_file:
            self.append_log(f'latest file is {newest_file}')
            download(newest_file, self.config.destination)
            return f'downloaded {newest_file} to {self.config.destination}'
        else:
            raise ValueError(f'No files found in {self.config.source}')

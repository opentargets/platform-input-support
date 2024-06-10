from dataclasses import dataclass
from typing import Any

from platform_input_support.action import Action, ActionConfigMapping
from platform_input_support.helpers.google import google
from platform_input_support.manifest.manifest import report_to_manifest
from platform_input_support.scratch_pad import scratch_pad


@dataclass
class FindLatestConfigMapping(ActionConfigMapping):
    source: str
    scratch_pad_key: str


class FindLatest(Action):
    def __init__(self, config: dict[str, Any]):
        self.config: FindLatestConfigMapping
        super().__init__(config)

    @report_to_manifest
    def run(self):
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
            scratch_pad.store(self.config.scratch_pad_key, newest_file)
            return
        else:
            raise ValueError(f'No files found in {self.config.source}')

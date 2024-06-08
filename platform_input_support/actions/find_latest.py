from dataclasses import dataclass
from typing import Any

from platform_input_support.action.action import Action, ActionConfigMapping
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
        scratch_pad.store(self.config.scratch_pad_key, 'testurlvalue')

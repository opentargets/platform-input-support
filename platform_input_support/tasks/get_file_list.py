from dataclasses import dataclass

from platform_input_support.config.models import TaskMapping
from platform_input_support.helpers.google import google
from platform_input_support.manifest import report_to_manifest
from platform_input_support.scratch_pad import scratch_pad
from platform_input_support.task import Task


@dataclass
class GetFileListMapping(TaskMapping):
    source: str
    pattern: str
    scratch_pad_key: str


class GetFileList(Task):
    def __init__(self, config: TaskMapping):
        self.config: GetFileListMapping
        super().__init__(config)

    @report_to_manifest
    def run(self):
        file_list: list[str] = []

        if self.config.pattern.startswith('!'):
            file_list = google.list(self.config.source, exclude=self.config.pattern[1:])
        else:
            file_list = google.list(self.config.source, include=self.config.pattern)

        if len(file_list):
            scratch_pad.store(self.config.scratch_pad_key, file_list)
            return f'{len(file_list)} files with pattern {self.config.pattern} found in {self.config.source}'
        else:
            raise ValueError(f'no files found in {self.config.source} with pattern {self.config.pattern}')

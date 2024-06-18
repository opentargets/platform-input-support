from dataclasses import dataclass

from platform_input_support.config.models import TaskMapping
from platform_input_support.helpers import google_helper
from platform_input_support.manifest.reporters import report_to_manifest
from platform_input_support.task import Task
from platform_input_support.util import scratchpad


@dataclass
class GetFileListMapping(TaskMapping):
    source: str
    pattern: str
    scratchpad_key: str


class GetFileList(Task):
    def __init__(self, config: TaskMapping):
        super().__init__(config)
        self.config: GetFileListMapping

    @report_to_manifest
    def run(self):
        source, pattern = self.config.source, self.config.pattern
        file_list: list[str] = []

        if pattern.startswith('!'):
            file_list = google_helper.list(source, exclude=pattern[1:])
        else:
            file_list = google_helper.list(source, include=pattern)

        if len(file_list):
            scratchpad.store(self.config.scratchpad_key, file_list)
            return f'{len(file_list)} files with pattern {pattern} found in {source}'
        else:
            raise ValueError(f'no files found in {source} with pattern {pattern}')

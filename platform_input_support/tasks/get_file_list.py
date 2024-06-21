from dataclasses import dataclass

from platform_input_support.config import scratchpad
from platform_input_support.config.models import TaskDefinition
from platform_input_support.helpers import google_helper
from platform_input_support.manifest import report_to_manifest
from platform_input_support.task import PreTask


@dataclass
class GetFileListDefinition(TaskDefinition):
    is_pre: bool = True
    source: str
    pattern: str
    sentinel: str


class GetFileList(PreTask):
    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: GetFileListDefinition

    @report_to_manifest
    def run(self):
        source, pattern, sentinel = self.definition.source, self.definition.pattern, self.definition.sentinel
        file_list: list[str] = []

        if pattern.startswith('!'):
            file_list = google_helper.list(source, exclude=pattern[1:])
        else:
            file_list = google_helper.list(source, include=pattern)

        if len(file_list):
            scratchpad.store(sentinel, file_list)
            return f'{len(file_list)} files with pattern `{pattern}` found in `{source}`'
        else:
            raise ValueError(f'no files found in `{source}` with pattern `{pattern}`')

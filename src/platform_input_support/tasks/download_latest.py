"""Download the file with the latest modification date among those in a prefix URI."""

from dataclasses import dataclass
from threading import Event
from typing import Self

from loguru import logger

from platform_input_support.helpers import get_remote_storage
from platform_input_support.helpers.download import download
from platform_input_support.tasks import Resource, Task, TaskDefinition, report


@dataclass
class DownloadLatestDefinition(TaskDefinition):
    """Configuration fields for the download_latest task.

    This task has the following custom configuration fields:
        - source str: The prefix from where the file with the latest modification date will
            be downloaded.
        - pattern str: Optional. The pattern to match files against. The pattern should be
            a simple string match, preceded by an exclamation mark to exclude files. For
            example, 'foo' will match all files containing 'foo', while '!foo' will exclude
            all files containing 'foo'.
    """

    source: str
    pattern: str | None = None


class DownloadLatest(Task):
    """Download the file with the latest modification date among those in a prefix URI."""

    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: DownloadLatestDefinition

    @report
    def run(self, *, abort: Event) -> Self:
        destination, source = self.definition.destination, self.definition.source

        remote_storage = get_remote_storage(self.definition.source)
        files = remote_storage.list(source, self.definition.pattern)
        if not files:
            raise ValueError(f'no files found in {self.definition.source} with pattern {self.definition.pattern}')

        newest_file = files.pop(0)

        if len(files):
            mtime = remote_storage.stat(newest_file)['mtime']

            for file in files:
                new_mtime = remote_storage.stat(file).get('mtime', 0)
                if remote_storage.stat(file).get('mtime', 0) > mtime:
                    newest_file = file
                    mtime = new_mtime

        logger.info(f'latest file is {newest_file}')
        download(newest_file, destination)
        self.resource = Resource(source=newest_file, destination=str(destination))
        logger.info('download successful')
        return self

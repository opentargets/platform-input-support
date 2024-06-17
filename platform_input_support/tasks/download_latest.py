from dataclasses import dataclass

from platform_input_support.config.models import TaskMapping
from platform_input_support.helpers import google_helper
from platform_input_support.helpers.download import DownloadHelper
from platform_input_support.manifest.reporters import report_to_manifest
from platform_input_support.task.task import Task


@dataclass
class DownloadLatestMapping(TaskMapping):
    source: list[str] | str
    destination: str


class DownloadLatest(Task):
    def __init__(self, config: TaskMapping):
        super().__init__(config)
        self.config: DownloadLatestMapping

    @report_to_manifest
    def run(self):
        file_list = self.config.source

        if isinstance(self.config.source, str):
            file_list = google_helper.list(self.config.source)

        newest_date = None
        newest_file = None

        for f in file_list:
            modification_date = google_helper.get_modification_date(f)
            if modification_date:
                if not newest_date or modification_date > newest_date:
                    newest_date = modification_date
                    newest_file = f

        if newest_file:
            self.append_log(f'latest file is {newest_file}')
            d = DownloadHelper(newest_file, self.config.destination)
            return d.download()
        else:
            raise ValueError(f'no files found in {self.config.source}')

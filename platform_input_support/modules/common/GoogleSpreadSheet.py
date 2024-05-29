import csv
import gspread
import logging
from abc import abstractmethod, ABC
from platform_input_support.manifest import get_manifest_service, ManifestStatus, ManifestResource

logger = logging.getLogger(__name__)


# Factory method
def get_spreadsheet_handler(spreadsheet_id,
                            worksheet_name,
                            path_output,
                            output_format='csv',
                            gcp_credentials=None):
    if gcp_credentials is None:
        return NoneAuthHandler(spreadsheet_id, worksheet_name, path_output, output_format)
    return AuthHandler(spreadsheet_id, worksheet_name, path_output, output_format, gcp_credentials)


class GoogleSpreadSheet(ABC):
    def __init__(self,
                 spreadsheet_id,
                 worksheet_name,
                 path_output,
                 output_format='csv',
                 gcp_credentials=None, base_url='https://docs.google.com/spreadsheets/d',
                 attempts=3):
        self._base_url = base_url
        self._gcp_credentials = gcp_credentials
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        self.path_output = path_output
        self.output_format = output_format
        self.attempts = attempts
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def _do_download(self) -> ManifestResource:
        pass

    @property
    def summary(self) -> str:
        return "Google Spreadsheet ID '{}', Worksheet name '{}', format '{}', destination PATH '{}'" \
            .format(self.spreadsheet_id, self.worksheet_name, self.output_format, self.path_output)

    def get_writer(self, f):
        # TODO - This implementation only returns a CSV writer, extend it in the future, e.g. for TSV, etc
        return csv.writer(f)

    def download(self) -> ManifestResource:
        return self._do_download()

    @staticmethod
    def get_spreadsheet_url(spreadsheet_id: str = ""):
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"


class AuthHandler(GoogleSpreadSheet):
    def _do_download(self) -> ManifestResource:
        self.logger.info("Authenticated Google Spreadsheet data collection for {}".format(self.summary))
        download_manifest = get_manifest_service().new_resource()
        download_manifest.source_url = self.get_spreadsheet_url(self.spreadsheet_id)
        download_manifest.path_destination = self.path_output
        for _ in range(self.attempts):
            try:
                gs_handler = gspread.service_account(filename=self._gcp_credentials)
                spreadsheet = gs_handler.open_by_key(self.spreadsheet_id)
                worksheet = spreadsheet.worksheet(self.worksheet_name)
                with open(self.path_output, 'w') as f:
                    writer = self.get_writer(f)
                    writer.writerows(worksheet.get_all_values())
            except Exception as e:
                self.logger.error(e)
                continue
            else:
                download_manifest.msg_completion = f"Spreadsheet data downloaded from its worksheet with name '{self.worksheet_name}'"
                download_manifest.status_completion = ManifestStatus.COMPLETED
                break
        if download_manifest.status_completion != ManifestStatus.COMPLETED:
            download_manifest.msg_completion = f"FAILED to download data from Google Spreadsheet with ID '{self.spreadsheet_id}', worksheet name '{self.worksheet_name}'"
            download_manifest.status_completion = ManifestStatus.FAILED
            self.logger.error(download_manifest.msg_completion)
        return download_manifest


class NoneAuthHandler(GoogleSpreadSheet):
    def _do_download(self):
        raise NotImplementedError(
            "NOT IMPLEMENTED - Anonymous Google Srpeadsheet data collection for {}".format(self.summary))

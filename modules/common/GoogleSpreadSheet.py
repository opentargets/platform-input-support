import csv
import gspread
import logging
from abc import abstractmethod, ABC

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
                 gcp_credentials=None, base_url='https://docs.google.com/spreadsheets/d'):
        self._base_url = base_url
        self._gcp_credentials = gcp_credentials
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        self.path_output = path_output
        self.output_format = output_format
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def _do_download(self):
        pass

    @property
    def summary(self):
        return "Google Spreadsheet ID '{}', Worksheet name '{}', format '{}', destination PATH '{}'" \
            .format(self.spreadsheet_id, self.worksheet_name, self.output_format, self.path_output)

    def get_writer(self, f):
        # TODO - This implementation only returns a CSV writer, extend it in the future, e.g. for TSV, etc
        return csv.writer(f)

    def download(self):
        self._do_download()


class AuthHandler(GoogleSpreadSheet):
    def _do_download(self):
        self.logger.info("Authenticated Google Spreadsheet data collection for {}".format(self.summary))
        try:
            gs_handler = gspread.service_account(filename=self._gcp_credentials)
            spreadsheet = gs_handler.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(self.worksheet_name)
            with open(self.path_output, 'w') as f:
                writer = self.get_writer(f)
                writer.writerows(worksheet.get_all_values())
        except Exception as e:
            self.logger.error(e)
            raise


class NoneAuthHandler(GoogleSpreadSheet):
    def _do_download(self):
        raise NotImplementedError(
            "NOT IMPLEMENTED - Anonymous Google Srpeadsheet data collection for {}".format(self.summary))

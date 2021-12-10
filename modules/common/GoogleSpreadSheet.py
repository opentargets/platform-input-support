import requests
import logging

logger = logging.getLogger(__name__)


class GoogleSpreadSheet(object):

    def __init__(self, output_dir, server ='https://docs.google.com/spreadsheets/d'):
        self.server = server
        self.output_type = 'tsv'
        self.output_dir = output_dir

    def download_as_csv(self, spreadsheet_info):
        uri = "{}/{}/export?format={}&gid={}".format(self.server, spreadsheet_info.gkey, self.output_type,spreadsheet_info.gid)
        logger.info(uri)
        response = requests.get(uri)
        filename =self.output_dir + '/' + spreadsheet_info.output_filename
        with open(filename, mode='wb') as localfile:
            localfile.write(response.content)

        return filename

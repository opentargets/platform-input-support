import os
import logging
import requests

logger = logging.getLogger(__name__)


class GoogleSpreadSheet(object):

    def __init__(self, output_dir, server='https://docs.google.com/spreadsheets/d'):
        self.server = server
        self.output_type = 'tsv'
        self.output_dir = output_dir

    def download_as_csv(self, spreadsheet_info):
        """
        Download the Google Spreadsheet desribed by the given details in the configured format

        :param spreadsheet_info: spreadsheet information object
        :return: destination path for downloaded spreadsheet file
        """
        uri = "{}/{}/export?format={}&gid={}".format(self.server, spreadsheet_info.gkey, self.output_type,
                                                     spreadsheet_info.gid)
        dst_path_file = os.path.join(self.output_dir, spreadsheet_info.output_filename)
        msg_download_info = "Google Spreadsheet URI '{}', download to '{}'".format(uri, dst_path_file)
        try:
            response = requests.get(uri)
        except requests.exceptions.RequestException as e:
            logger.error("Could not retrieve {}, due to ERROR '{}'".format(msg_download_info, e))
        else:
            if response.status_code == requests.codes.ok:
                # NOTE We should also catch a possible error when writing the local file. I haven't done it here because
                # it's everywhere we use 'with', and I don't want to overcomplicate this module right now.
                with open(dst_path_file, mode='wb') as localfile:
                    localfile.write(response.content)
                    logger.info(msg_download_info)
            else:
                logger.error("Could not retrieve {}, due to response code '{}'".format(msg_download_info, response.status_code))
        return dst_path_file

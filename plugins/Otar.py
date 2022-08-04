import os
import logging

from yapsy.IPlugin import IPlugin
from modules.common import create_folder
from modules.common.GoogleSpreadSheet import get_spreadsheet_handler

logger = logging.getLogger(__name__)

"""
This module gathers all data related to OTAR Projects (metadata and mapping)
"""


class Otar(IPlugin):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process(self, conf, output, cmd_conf=None):
        self.logger.info("OTAR Projects data collection - START -")
        gcp_credentials = conf.google_credential_key
        dst_folder = os.path.join(output.prod_dir, conf.gs_output_dir)
        self.logger.debug("Prepare destination folder at '{}'".format(dst_folder))
        create_folder(dst_folder)
        if gcp_credentials is None:
            self.logger.warning("NO GCP credentials have been provided")
        for sheet in conf.sheets:
            path_dst = os.path.join(dst_folder, sheet.output_filename)
            handler = get_spreadsheet_handler(sheet.id_spreadsheet,
                                              sheet.worksheet_name,
                                              path_dst,
                                              sheet.output_format,
                                              gcp_credentials)
            handler.download()
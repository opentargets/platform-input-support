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
        self._logger = logging.getLogger(__name__)

    def process(self, conf, output, cmd_conf=None):
        self._logger.info("[STEP] BEGIN, otar")
        gcp_credentials = conf.gcp_credentials
        dst_folder = os.path.join(output.prod_dir, conf.gs_output_dir)
        self._logger.debug("Prepare destination folder at '{}'".format(dst_folder))
        create_folder(dst_folder)
        if gcp_credentials is None:
            self._logger.error("NO GCP credentials have been provided")
        # TODO - Parallelize this
        for sheet in conf.sheets:
            path_dst = os.path.join(dst_folder, sheet.output_filename)
            handler = get_spreadsheet_handler(sheet.id_spreadsheet,
                                              sheet.worksheet_name,
                                              path_dst,
                                              sheet.output_format,
                                              gcp_credentials)
            handler.download()
        self._logger.info("[STEP] END, otar")
import os
import logging

from yapsy.IPlugin import IPlugin
from modules.common import create_folder
from manifest import ManifestStatus, get_manifest_service
from modules.common.GoogleSpreadSheet import get_spreadsheet_handler

logger = logging.getLogger(__name__)

"""
This module gathers all data related to OTAR Projects (metadata and mapping)
"""

class Otar(IPlugin):
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.step_name = "OTAR"

    @staticmethod
    def __get_spreadsheet_url(spreadsheet_id: str = ""):
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

    def process(self, conf, output, cmd_conf=None):
        self._logger.info("[STEP] BEGIN, otar")
        manifest_step = get_manifest_service().get_step(self.step_name)
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
            download_manifest = get_manifest_service().new_resource()
            download_manifest.source_url = self.__get_spreadsheet_url(sheet.id_spreadsheet)
            download_manifest.path_destination = path_dst
            download_manifest.msg_completion = f"Source URL is the Spreadsheet," \
                                               f" data downloaded from its worksheet with name '{sheet.worksheet_name}'"
            get_manifest_service().compute_checksums(manifest_step.resources)
            if not get_manifest_service().are_all_resources_complete(manifest_step.resources):
                manifest_step.status_completion = ManifestStatus.FAILED
                manifest_step.msg_completion = "COULD NOT retrieve all the resources"
            # TODO - Validation
            if manifest_step.status_completion != ManifestStatus.FAILED:
                manifest_step.status_completion = ManifestStatus.COMPLETED
                manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, otar")

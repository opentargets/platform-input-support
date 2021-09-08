"""
This module gathers all data related to OpenFDA FAERS database, with a focus on Drug Events.

In addition, a collection of blacklisted events is downloaded for later use in the ETL backend pipeline.
"""

import os
import zipfile
import logging
import warnings

from definitions import PIS_OUTPUT_OPENFDA
from .DownloadResource import DownloadResource
from datetime import datetime

logger = logging.getLogger(__name__)

class OpenFDA(object):
    """
    This class implements the strategy for collection of OpenFDA FAERS drug event data and related information
    """

    def __init__(self, config) -> None:
        self.config = config
        self.write_date = datetime.today().strftime('%Y-%m-%d')

    # TODO
    def _download_openfda_faers(self, resource):
        logger.info("OpenFDA available files download, URI '{}' --- START ---".format(resource.uri))
    
    # TODO
    def _download_blacklist(self, resource):
        logger.info("OpenFDA blacklisted events download, URI '{}' --- START ---".format(resource.uri))
        downloader = DownloadResource(PIS_OUTPUT_OPENFDA)
        download = downloader.execute_download(resource)
        downloaded_files = dict()
        if resource.unzip_file:
            logger.error("UNSUPPORTED file format (ZIP) - URI '{}'".format(resource.uri))
        else:
            if download:
                downloaded_files[download] = {
                    'resource': resource.resource,
                    'gs_output_dir': os.path.join(PIS_OUTPUT_OPENFDA, resource.output_filename)
                }
        return downloaded_files

    # TODO - Step body
    def run(self):
        logger.info("OpenFDA ETL --- START ---")
        downloaded_files = dict()
        for download_entry in self.config["datasources"]["downloads"]:
            if "blacklisted" in download_entry.resource:
                downloaded_files.update(self._download_blacklist(download_entry))
            elif "available" in download_entry.resource:
                downloaded_files.update(self._download_openfda_faers(download_entry))
            else:
                logger.warning("UNSUPPORTED OpenFDA download resource '{}', URI '{}'".format(download_entry.resource, download_entry.uri))
        return downloaded_files

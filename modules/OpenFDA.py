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
        pass
    
    # TODO
    def _download_blacklist(self, resource):
        pass

    # TODO - Step body
    def run(self):
        logger.info("OpenFDA ETL --- START ---")
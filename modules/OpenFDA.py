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


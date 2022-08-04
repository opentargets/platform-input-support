import logging
from yapsy.IPlugin import IPlugin

logger = logging.getLogger(__name__)

"""
This module gathers all data related to OTAR Projects (metadata and mapping)
"""


class Otar(IPlugin):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process(self, conf, output, cmd_conf=None):
        self.logger.info("OTAR Projects data collection - START -")
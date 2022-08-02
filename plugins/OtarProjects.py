import logging
from yapsy.IPlugin import IPlugin

logger = logging.getLogger(__name__)

"""
This module gathers all data related to OTAR Projects (metadata and mapping)
"""


class OtarProjects(IPlugin):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process(self, conf, output, cmd_conf=None):
        # TODO
        pass
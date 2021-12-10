import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads
logger = logging.getLogger(__name__)

"""

"""
class Evidence(IPlugin):
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def process(self, conf, output, cmd_conf):
        self._logger.info("Evidence step")
        Downloads(output.prod_dir).exec(conf)
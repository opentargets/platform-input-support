import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads
logger = logging.getLogger(__name__)

"""

"""
class Reactome(IPlugin):
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def process(self, conf, outputs, cmd_conf):
        self._logger.info("Reactome step")
        Downloads(outputs.prod_dir).exec(conf)
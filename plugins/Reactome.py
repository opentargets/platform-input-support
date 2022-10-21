import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads

logger = logging.getLogger(__name__)


class Reactome(IPlugin):
    """
    Reactome pipeline step plug-in
    """
    def __init__(self):
        """
        Constructor, prepare the logging subsystem
        """
        self._logger = logging.getLogger(__name__)

    def process(self, conf, outputs, cmd_conf=None):
        """
        Reactome data collection step implementation

        :param conf: step configuration object
        :param outputs: output location information object for step results
        :param cmd_conf: NOT USED
        """
        self._logger.info("[STEP] BEGIN, reactome")
        Downloads(outputs.prod_dir).exec(conf)
        self._logger.info("[STEP] END, reactome")

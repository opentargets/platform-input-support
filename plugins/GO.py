import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads

logger = logging.getLogger(__name__)


class GO(IPlugin):
    """
    GO pipeline step implementation
    """
    def __init__(self):
        """
        Constructor, prepare the logging subsystem
        """
        self._logger = logging.getLogger(__name__)

    def process(self, conf, output, cmd_conf=None):
        """
        GO data collection pipeline step implementation

        :param conf: step configuration object
        :param output: data collection destination information object
        :param cmd_conf: NOT USED
        """
        self._logger.info("[STEP] BEGIN, GO")
        Downloads(output.prod_dir).exec(conf)
        self._logger.info("[STEP] END, GO")

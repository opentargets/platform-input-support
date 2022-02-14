import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads

logger = logging.getLogger(__name__)


class Evidence(IPlugin):
    """
    Evidence data collection step implementation
    """
    def __init__(self):
        """
        Constructor, it prepares the logging subsystem
        """
        self._logger = logging.getLogger(__name__)

    def process(self, conf, output, cmd_conf=None):
        """
        Evidence pipeline step implementation

        :param conf: step configuration object
        :param output: output folder information
        :param cmd_conf: UNUSED
        """
        self._logger.info("Evidence step")
        Downloads(output.prod_dir).exec(conf)

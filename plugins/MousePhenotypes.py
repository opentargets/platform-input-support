import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads

logger = logging.getLogger(__name__)


class MousePhenotypes(IPlugin):
    """
    Mouse Phenotypes pipeline step
    """
    def __init__(self):
        """
        Constructor, prepare logging subsystem
        """
        self._logger = logging.getLogger(__name__)

    def process(self, conf, output, cmd_conf=None):
        """
        Pipeline step implementation

        :param conf: step configuration object
        :param output: destination information for the results of this step
        :param cmd_conf: NOT USED
        """
        self._logger.info("MousePhenotypes step")
        Downloads(output.prod_dir).exec(conf)

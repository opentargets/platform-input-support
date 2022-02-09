import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads

logger = logging.getLogger(__name__)


class Interactions(IPlugin):
    """
    Interaction data collection step
    """
    def __init__(self):
        """
        Constructor, prepare logging subsystem
        """
        self._logger = logging.getLogger(__name__)

    def process(self, conf, output, cmd_conf=None):
        """
        Interaction pipeline step implementation

        :param conf: step configuration object
        :param output: output information object on where the results of this step should be placed
        :param cmd_conf: NOT USED
        """
        self._logger.info("Interactions step")
        Downloads(output.prod_dir).exec(conf)

import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads
from manifest import ManifestStatus, get_manifest_service

logger = logging.getLogger(__name__)


class Literature(IPlugin):
    """
    Literature EuropePMC data collection step
    """
    def __init__(self):
        """
        Constructor, prepare logging subsystem
        """
        self._logger = logging.getLogger(__name__)
        self.step_name = "Literature"

    def process(self, conf, output, cmd_conf=None):
        """
        Literature pipeline step

        :param conf: step configuration object
        :param output: output information object on where the results of this step should be placed
        :param cmd_conf: NOT USED
        """
        self._logger.info("[STEP] BEGIN, Literature")
        manifest_service = get_manifest_service()
        manifest_step = manifest_service.get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        manifest_step.status_completion = ManifestStatus.COMPLETED
        manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, Literature")

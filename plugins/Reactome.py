import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads
from manifest import ManifestStatus, get_manifest_service

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
        self.step_name = "Reactome"

    def process(self, conf, outputs, cmd_conf=None):
        """
        Reactome data collection step implementation

        :param conf: step configuration object
        :param outputs: output location information object for step results
        :param cmd_conf: NOT USED
        """
        self._logger.info("[STEP] BEGIN, reactome")
        manifest_service = get_manifest_service()
        manifest_step = manifest_service.get_step(self.step_name)
        manifest_step.resources.extend(Downloads(outputs.prod_dir).exec(conf))
        manifest_step.status_completion = ManifestStatus.COMPLETED
        manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, reactome")

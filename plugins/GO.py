import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads
from manifest import ManifestStatus, get_manifest_service

logger = logging.getLogger(__name__)


class GO(IPlugin):
    """
    GO pipeline step implementation
    """
    def __init__(self):
        """
        Constructor, prepare the logging subsystem
        """
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self.step_name = "GO"

    def process(self, conf, output, cmd_conf=None):
        """
        GO data collection pipeline step implementation

        :param conf: step configuration object
        :param output: data collection destination information object
        :param cmd_conf: NOT USED
        """
        self._logger.info("[STEP] BEGIN, GO")
        manifest_step = get_manifest_service().get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        get_manifest_service().compute_checksums(manifest_step.resources)
        manifest_step.status_completion = ManifestStatus.COMPLETED
        manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, GO")

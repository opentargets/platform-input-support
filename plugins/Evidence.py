import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads
from manifest import ManifestStatus, get_manifest_service

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
        self.step_name = "Evidence"

    def process(self, conf, output, cmd_conf=None):
        """
        Evidence pipeline step implementation

        :param conf: step configuration object
        :param output: output folder information
        :param cmd_conf: UNUSED
        """
        self._logger.info("[STEP] BEGIN, Evidence")
        manifest_service = get_manifest_service()
        manifest_step = manifest_service.get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        get_manifest_service().compute_checksums(manifest_step.resources)
        manifest_step.status_completion = ManifestStatus.COMPLETED
        manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, Evidence")

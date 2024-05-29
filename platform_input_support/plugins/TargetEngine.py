import logging
from yapsy.IPlugin import IPlugin

from platform_input_support.modules.common.Downloads import Downloads
from platform_input_support.manifest import get_manifest_service, ManifestStatus


class TargetEngine(IPlugin):
    """
    TargetEngine pipeline step
    """
    def __init__(self):
        """
        Constructor, prepare logging subsystem and step name
        """
        self._logger = logging.getLogger(__name__)
        self.step_name = "TargetEngine"

    def process(self, conf, output, cmd_conf=None):
        """
        TargetEngine data collection pipeline step implementation

        :param conf: step configuration object
        :param output: output information object for the results of this pipeline step
        :param cmd_conf: command line tools configuration object
        """
        self._logger.info("[STEP] BEGIN, TargetEngine")
        manifest_step = get_manifest_service().get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        get_manifest_service().compute_checksums(manifest_step.resources)
        if get_manifest_service().are_all_resources_complete(manifest_step.resources):
            manifest_step.status_completion = ManifestStatus.COMPLETED
            manifest_step.msg_completion = "The step has completed its execution"
        else:
            manifest_step.status_completion = ManifestStatus.FAILED
            manifest_step.msg_completion = "The step has failed its execution, some resources are not complete"
            self._logger.error(manifest_step.msg_completion)
        # TODO - Validation
        self._logger.info("[STEP] END, TargetEngine")
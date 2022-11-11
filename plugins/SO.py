import os
import logging
from yapsy.IPlugin import IPlugin
from modules.common.Riot import Riot
from modules.common import create_folder
from modules.common.Downloads import Downloads
from manifest import ManifestStatus, get_manifest_service

logger = logging.getLogger(__name__)



class SO(IPlugin):
    """
    SO ontology pipeline step
    """
    def __init__(self):
        """
        Constructor, prepare logging subsystem
        """
        self._logger = logging.getLogger(__name__)
        self.step_name = "SO"

    def process(self, conf, output, cmd_conf):
        """
        SO ontology data collection pipeline step implementation

        :param conf: step configuration object
        :param output: output information object for the results of this pipeline step
        :param cmd_conf: command line tools configuration object
        """
        self._logger.info("[STEP] BEGIN, so")
        manifest_step = get_manifest_service().get_step(self.step_name)
        riot = Riot(cmd_conf)
        download_manifest = Downloads.download_staging_http(output.staging_dir, conf.etl)
        file_ouput_path = os.path.join(output.prod_dir, conf.etl.path)
        create_folder(file_ouput_path)
        download_manifest.path_destination = riot.convert_owl_to_jsonld(download_manifest.path_destination,
                                                                        file_ouput_path,
                                                                        conf.etl.owl_jq)
        download_manifest.msg_completion = f"Original converted to JSON and filter with JQ using '{conf.etl.owl_jq}'"
        download_manifest.status_completion = ManifestStatus.COMPLETED
        manifest_step.resources.append(download_manifest)
        manifest_step.status_completion = ManifestStatus.COMPLETED
        manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, so")
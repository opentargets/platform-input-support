import os
from pathlib import Path
import tempfile
from typing import Dict
import logging
from platform_input_support.modules.common.Utils import Utils, subproc, CustomSubProcException

logger = logging.getLogger(__name__)


class RiotException(Exception):
    pass


class Riot(object):
    def __init__(self, yaml):
        self.yaml = yaml
        self._jq_cmd = None
        self._riot_cmd = None

    @property
    def riot_cmd(self):
        if self._riot_cmd is None:
            self._riot_cmd = Utils.check_path_command("riot", self.yaml.riot)
        return self._riot_cmd

    @property
    def jq_cmd(self):
        if self._jq_cmd is None:
            self._jq_cmd = Utils.check_path_command("jq", self.yaml.jq)
        return self._jq_cmd

    def get_running_environment(self) -> Dict[str, str]:
        """Return the environment.
        JVM options from the yaml config are passed in here.
        """
        os.environ["_JAVA_OPTIONS"] = str(self.yaml.java_vm)
        logger.info("_JAVA_OPTIONS: " + os.environ["_JAVA_OPTIONS"])
        return os.environ.copy()

    def run_riot(
        self,
        owl_file: Path,
        dir_output: Path,
        json_file: Path,
        owl_jq: str,
    ) -> str:
        """
        Convert the given OWL file into JSON-LD with a filtering step on the produced JSON-LD by the given filter

        :param owl_file: OWL file to convert
        :param dir_output: destination folder for OWL conversion
        :param json_file: destination json file name for OWL conversion
        :param owl_jq: JQ filtering for the JSON-LD conversion of the OWL file
        :return: string repr of destination file path of the conversion + filtering for the given OWL file
        """
        path_output = os.path.join(dir_output, json_file)
        with tempfile.NamedTemporaryFile() as riot_outfile:
            riot_cmd = f"{self.riot_cmd} --output JSON-LD {owl_file} > {riot_outfile.name}"
            jq_cmd = f"{self.jq_cmd} -r '{owl_jq}' {riot_outfile.name} > {path_output}"
            try:
                subproc(cmd=riot_cmd, env=self.get_running_environment())
                logger.debug("riot command completed.")
                subproc(cmd=jq_cmd)
                logger.debug("jq command completed.")
            except CustomSubProcException as err:
                msg_err = (f"FAILED to run RIOT on file '{owl_file}' "
                           f"and JQ with filter '{owl_jq}' "
                           f"due to the following error: '{err}'")
                logger.error(msg_err)
                raise RiotException(msg_err) from err
        return path_output

    def convert_owl_to_jsonld(self, owl_file, output_dir, owl_jq):
        """
        Convert a given OWL file to JSON-LD filtering its content by the given JQ filter

        :param owl_file: source OWL file
        :param output_dir: destination folder for JSON-LD conversion
        :param owl_jq: JQ filter to apply to JSON-LD converted content
        :return: destination file path for the converted and filtered OWL content
        """
        path, filename = os.path.split(owl_file)
        dst_filename = filename.replace(".owl", ".json")
        logger.debug(
            "RIOT OWL file '{}' to JSON, output folder '{}', destination file name '{}', JQ filter '{}'".format(
                owl_file, output_dir, dst_filename, owl_jq
            )
        )
        return self.run_riot(owl_file, output_dir, dst_filename, owl_jq)

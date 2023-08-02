import os
from pathlib import Path
import logging
import subprocess
from modules.common.Utils import Utils

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

    def configure_jvm(self) -> None:
        """Configure the JVM environment varaiables based on the
        yaml file.
        """
        os.environ["_JAVA_OPTIONS"] = str(self.yaml.java_vm)
        logger.info("_JAVA_OPTIONS: " + os.environ["_JAVA_OPTIONS"])

    def run_riot(
        self,
        owl_file: Path,
        dir_output: Path,
        json_file: Path,
        owl_jq: str,
    ):
        """
        Convert the given OWL file into JSON-LD with a filtering step on the produced JSON-LD by the given filter

        :param owl_file: OWL file to convert
        :param dir_output: destination folder for OWL conversion
        :param json_file: destination json file name for OWL conversion
        :param owl_jq: JQ filtering for the JSON-LD conversion of the OWL file
        :return: destination file path of the conversion + filtering for the given OWL file
        """
        path_output = os.path.join(dir_output, json_file)
        # Set JVM memory limits
        self.configure_jvm()
        riot_jq_cmd_string = (
            f"{self.riot_cmd} -v --output JSON-LD {owl_file} | "
            f"{self.jq_cmd} -r '{owl_jq}' > {path_output}"
        )
        try:
            riot_jq = subprocess.run(
                riot_jq_cmd_string,
                env=os.environ.copy(),
                shell=True,
                text=True,
                capture_output=True,
                check=False,
            )
            riot_jq.check_returncode()
        except subprocess.CalledProcessError as err:
            msg_err = f"The following error occurred: '{err}'"
            logger.error(msg_err)
            raise RiotException(msg_err)
        if "error" in riot_jq.stderr:
            logger.error(riot_jq.stderr)
            raise RiotException(riot_jq.stderr)
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

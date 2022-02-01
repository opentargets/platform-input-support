import os
import errno
import logging
import subprocess
from modules.common.Utils import Utils

logger = logging.getLogger(__name__)


class Riot(object):

    def __init__(self, yaml):
        self.yaml = yaml

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

    @property
    def jvm_args(self):
        if self._jvm_args is None:
            os.environ["JVM_ARGS"] = str(self.yaml.java_vm)
            logger.info("JVM_ARGS: " + os.environ["JVM_ARGS"])
            self._jvm_args = str(self.yaml.java_vm)
        return self._jvm_args

    def run_riot(self, owl_file, dir_output, json_file, owl_jq):
        """
        Convert the given OWL file into JSON-LD with a filtering step on the produced JSON-LD by the given filter

        :param owl_file: OWL file to convert
        :param dir_output: destination folder for OWL conversion
        :param json_file: destination json file name for OWL conversion
        :param owl_jq: JQ filtering for the JSON-LD conversion of the OWL file
        :return: destination file path of the conversion + filtering for the given OWL file
        """
        output_path = os.path.join(dir_output, json_file)
        with open(output_path) as json_output, \
                subprocess.Popen([self.riot_cmd, "--output", "JSON-LD", owl_file],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE) as riot_process, \
                subprocess.Popen([self.jq_cmd, "-r", owl_jq],
                                 stdin=riot_process.stdout,
                                 stdout=subprocess.PIPE) as jq_process:
            json_output.write(jq_process.stdout.read())
        return output_path

    def convert_owl_to_jsonld(self, owl_file, output_dir, owl_qj):
        head, tail = os.path.split(owl_file)
        json_file = tail.replace(".owl", ".json")
        return self.run_riot(owl_file, output_dir, json_file, owl_qj)

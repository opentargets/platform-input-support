import os
import errno
import logging
import subprocess
from modules.common.Utils import Utils

logger = logging.getLogger(__name__)


class Riot(object):

    def __init__(self, yaml):
        self.yaml = yaml
        self._jq_cmd = None
        self._riot_cmd = None
        self._jvm_args = None

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
        path_output = os.path.join(dir_output, json_file)
        # Set JVM memory limits
        run_env = os.environ.copy()
        run_env["JAVA_OPTS"] = "-Xms2048m -Xmx8192m"
        try:
            with open(path_output, "wb") as json_output, \
                    subprocess.Popen([self.riot_cmd, "--output", "JSON-LD", owl_file], env=run_env,
                                     stdout=subprocess.PIPE) as riot_process, \
                    subprocess.Popen([self.jq_cmd, "-r", owl_jq], env=run_env,
                                     stdin=riot_process.stdout,
                                     stdout=subprocess.PIPE) as jq_process:
                json_output.write(jq_process.stdout.read())
        except EnvironmentError as e:
            logger.error("When running RIOT for OWL file '{}', "
                         "with destination path '{}' and JQ filter '{}', "
                         "the following error occurred: '{}'".format(owl_file, path_output, owl_jq, e))
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
        logger.debug("RIOT OWL file '{}' to JSON, output folder '{}', destination file name '{}', JQ filter '{}'"
                     .format(owl_file, output_dir, dst_filename, owl_jq))
        return self.run_riot(owl_file, output_dir, dst_filename, owl_jq)

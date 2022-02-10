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
        json_output = open(os.path.join(dir_output, json_file), "wb")
        try:
            riot_process = subprocess.Popen([self.riot_cmd, "--output", "JSON-LD", owl_file], stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE)
            jq_process = subprocess.Popen([self.jq_cmd, "-r", owl_jq], stdin=riot_process.stdout,
                                          stdout=subprocess.PIPE)
            json_output.write(jq_process.stdout.read())
        except OSError as e:
            if e.errno == errno.ENOENT:
                # handle file not found error.
                logger.error(errno.ENOENT)
            else:
                # Something else went wrong
                raise
        finally:
            json_output.close()

        return json_output.name

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

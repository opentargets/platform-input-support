import logging
import subprocess
import errno
import os
from modules.common.Utils import Utils

logger = logging.getLogger(__name__)


class Riot(object):

    def __init__(self, yaml):
        self.yaml = yaml
        self.riot_cmd = Utils.check_path_command("riot", self.yaml.riot )
        self.jq_cmd = Utils.check_path_command("jq", self.yaml.jq )
        self.jvm_args = self.set_jvm_args()

    def set_jvm_args(self):
        os.environ["JVM_ARGS"] = str(self.yaml.java_vm)
        logger.info("JVM_ARGS: " + os.environ["JVM_ARGS"])
        return str(self.yaml.java_vm)

    def run_riot(self, owl_file, dir_output, json_file, owl_jq):
        json_output = open(dir_output + '/' + json_file, "wb")
        try:
            riot_process = subprocess.Popen([self.riot_cmd, "--output", "JSON-LD", owl_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            jq_process = subprocess.Popen([self.jq_cmd, "-r", owl_jq], stdin=riot_process.stdout, stdout=subprocess.PIPE)
            json_output.write(jq_process.stdout.read())
            json_output.close()
        except OSError as e:
            if e.errno == errno.ENOENT:
                # handle file not found error.
                logger.error(errno.ENOENT)
            else:
                # Something else went wrong
                raise

        return json_output.name

    def convert_owl_to_jsonld(self, owl_file, output_dir, owl_qj):
        head, tail = os.path.split(owl_file)
        json_file = tail.replace(".owl", ".json")
        return self.run_riot(owl_file, output_dir, json_file, owl_qj)


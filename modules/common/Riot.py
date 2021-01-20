import logging
import subprocess
import errno
import os
import shutil

logger = logging.getLogger(__name__)


class Riot(object):

    def __init__(self, yaml):
        self.yaml_config = yaml
        self.riot_cmd = self.check_path_command("riot", self.yaml_config.riot)
        self.jq_cmd = self.check_path_command("jq", self.yaml_config.jq)
        self.jvm_args =  self.set_jvm_args()

    def check_path_command(self, cmd, yaml_cmd):
        cmd_result = shutil.which(cmd)
        if cmd_result == None:
            # use the riot from the config file
            print(cmd+" not found. Using the path from config.yaml")
            cmd_result = yaml_cmd
        return cmd_result

    def set_jvm_args(self):
        #self.yaml_config
        os.environ["JVM_ARGS"] = str(self.yaml_config.java_vm)
        print("JVM_ARGS" + os.environ["JVM_ARGS"])

    def riot(self, owl_file, dir_output, json_file, owl_jq):
        jsonwrite = open(dir_output + '/' + json_file, "wb")
        try:
            riotp = subprocess.Popen([self.riot_cmd, "--output", "JSON-LD", owl_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            jqp = subprocess.Popen([self.jq_cmd, "-r", owl_jq], stdin=riotp.stdout, stdout=subprocess.PIPE)
            jsonwrite.write(jqp.stdout.read())
            jsonwrite.close()
        except OSError as e:
            if e.errno == errno.ENOENT:
                # handle file not found error.
                logger.error(errno.ENOENT)
            else:
                # Something else went wrong
                raise

        return jsonwrite.name


    def convert_owl_to_jsonld(self, owl_file, output_dir, owl_qj):
        head, tail = os.path.split(owl_file)
        json_file = tail.replace(".owl", ".json")
        return self.riot(owl_file, output_dir, json_file, owl_qj)


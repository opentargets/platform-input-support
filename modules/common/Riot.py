import errno
import logging
import os
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
        run_env["_JAVA_OPTIONS"] = "-Xms4096m -Xmx8192m"

        try:
            logger.info(f"running Riot on {owl_file} ...")
            riot_output = subprocess.run([self.riot_cmd, "--output", "JSON-LD", owl_file], env=run_env, capture_output=True)
            riot_output.check_returncode()               
                                
            # jq_output = subprocess.run([self.jq_cmd, "-r", owl_jq], input=riot_output.stdout, 
            #                 stdout=open(path_output, "wb"), stderr=subprocess.PIPE)
            logger.info(f"running JQ on Riot output ...")
            jq_output = subprocess.run([self.jq_cmd, "-r", owl_jq], input=riot_output.stdout, 
                                    capture_output= True)
            jq_output.check_returncode()
            with open(path_output, "wb") as json_output:
                json_output.write(jq_output.stdout)

            logger.info(f"--->jq_output size: {os.path.getsize(path_output)}")
            
        except subprocess.CalledProcessError as e:
            # logger.error(f"Error in running command {riot_output.args}: {e.stderr.decode('utf-8')} and this code: {e.returncode}")
            msg = "When running RIOT for OWL file '{}', \
                with destination path '{}' and JQ filter '{}', \
                    the following error occurred: '{}'".format(owl_file, path_output, owl_jq, e)
            if (e.returncode == 137):
                self._logger.error("Command was killed, possibly due to out of memory. \
                                   You may need to increase your VM's memory.")
            raise
        
        except OSError as e:            
            msg = "When running RIOT for OWL file '{}', \
                with destination path '{}' and JQ filter '{}', \
                    the following error occurred: '{}'".format(owl_file, path_output, owl_jq, e)
            logger.error(f"Error no: {e.errno}, Error str: {e.strerror}, Msg: {msg}")
            raise

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

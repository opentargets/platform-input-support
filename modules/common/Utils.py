import logging
import shutil
import subprocess
from addict import Dict
import os


logger = logging.getLogger(__name__)

#print(os.environ["PATH"])

class Utils(object):

    def __init__(self, config, outputs):
        self.config = config
        self.output_dir = outputs.prod_dir

    @staticmethod
    def check_path_command(cmd, yaml_cmd):
        cmd_result = shutil.which(cmd)
        if cmd_result is None:
            logger.info(cmd + " not found. Using the path from config.yaml")
            cmd_result = yaml_cmd
        logger.debug(f"{cmd} path {cmd_result}")
        return cmd_result

    def gsutil_multi_copy_to(self, destination_bucket):
        # print(os.environ["PATH"])
        # cmd_result = shutil.which("gsutil")
        # cmd = "gsutil -q -m cp -r " + self.yaml.output_dir + "/* gs://" + destination_bucket + "/"
        # subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        proc = subprocess.Popen(
            ["gsutil", "-m", "cp", "-r", self.output_dir + "/*", "gs://" + destination_bucket + "/"])
        try:
            outs, errs = proc.communicate()
        except:
            proc.kill()
            outs, errs = proc.communicate()

    @staticmethod
    def resource_for_stage(resource):
        resource_stage = Dict()
        resource_stage.path = ""
        resource_stage.uri = resource.uri
        resource_stage.output_filename = os.path.basename(resource.uri)
        return resource_stage

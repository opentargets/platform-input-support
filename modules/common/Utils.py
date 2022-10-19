import os
import shutil
import logging
import subprocess
from addict import Dict

logger = logging.getLogger(__name__)


# print(os.environ["PATH"])

class Utils(object):

    def __init__(self, config, outputs):
        self.config = config
        self.output_dir = outputs.prod_dir

    @staticmethod
    def check_path_command(cmd, yaml_cmd):
        """
        Establish the path for a particular command from either the system environment or the specified setting in the
        configuration file

        :param cmd: Command to establish the path for
        :param yaml_cmd: command's path set in the configuration file
        :return: the path for the given command
        """
        cmd_result = shutil.which(cmd)
        if cmd_result is None:
            cmd_result = yaml_cmd
            logger.warning("Command '{}' NOT FOUND. Using the path from config.yaml".format(cmd))
        logger.debug(f"'{cmd}' path '{cmd_result}'")
        return cmd_result

    def gsutil_multi_copy_to(self, destination_bucket):
        """
        Copy all files in the currently set output folder to the given Google Storage Bucket location

        :param destination_bucket: destination Google Storage Bucket location
        """
        # print(os.environ["PATH"])
        # cmd_result = shutil.which("gsutil")
        # cmd = "gsutil -q -m cp -r " + self.yaml.output_dir + "/* gs://" + destination_bucket + "/"
        # subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        logger.debug("gsutil_multi_copy_to - using gsutil for source '{}', destination '{}'"
                     .format(os.path.join(self.output_dir, "*"), "gs://{}/".format(destination_bucket)))
        proc = subprocess.Popen(["gsutil",
                                 "-m",
                                 "cp",
                                 "-r",
                                 os.path.join(self.output_dir, "*"),
                                 "gs://{}/".format(destination_bucket)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # I know, magic numbers
        completed = False
        for attempt in range(9):
            try:
                # Wait for 1 hour for the operation to complete
                _, err = proc.communicate(timeout=3600)
            except subprocess.TimeoutExpired:
                logger.error("Attempt #{} timed out!".format(attempt + 1))
                continue
            except Exception as e:
                proc.kill()
                logger.error(f"There was a problem copying files to bucket {destination_bucket}, ERROR '{e}'")
                break
            else:
                completed = True
                logger.info("gsutil copy for source '{}', destination '{}' completed!"
                            .format(os.path.join(self.output_dir, "*"), "gs://{}/".format(destination_bucket)))
                break
        if not completed:
            proc.kill()
            _, err = proc.communicate()
            logger.error(
                f"Could not complete file copy to GCP Bucket '{destination_bucket}', error output '{err.decode('utf-8')}'")

    @staticmethod
    def resource_for_stage(resource):
        """
        Build a resource stage description for the given information.

        :param resource: information to use for building the resource stage description
        :return: resource stage description
        """
        resource_stage = Dict()
        resource_stage.path = ""
        resource_stage.uri = resource.uri
        resource_stage.output_filename = os.path.basename(resource.uri)
        return resource_stage

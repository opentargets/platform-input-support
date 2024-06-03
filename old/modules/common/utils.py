import os
import shutil
import subprocess
from pathlib import Path

from addict import Dict
from loguru import logger


class Utils:
    def __init__(self, config, outputs):
        self.config = config
        self.output_dir = outputs.prod_dir

    @staticmethod
    def check_path_command(cmd, yaml_cmd):
        """Establish the path for a particular command.

        Gets the path from either the system environment or the specified setting in the
        configuration file.

        :param cmd: Command to establish the path for
        :param yaml_cmd: command's path set in the configuration file
        :return: the path for the given command
        """
        cmd_result = shutil.which(cmd)
        if cmd_result is None:
            cmd_result = yaml_cmd
            logger.warning(f'Command {cmd} NOT FOUND. Using the path from config.yaml')
        logger.debug(f'{cmd} path {cmd_result}')
        return cmd_result

    def gsutil_multi_copy_to(self, destination_bucket):
        """Copy all files in the currently set output folder to the given Google Storage Bucket location.

        :param destination_bucket: destination Google Storage Bucket location
        """
        # print(os.environ["PATH"])
        # cmd_result = shutil.which("gsutil")
        # cmd = "gsutil -q -m cp -r " + self.yaml.output_dir + "/* gs://" + destination_bucket + "/"
        # subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        source = os.path.join(self.output_dir, '*')
        destination_bucket = f'gs://{destination_bucket}/'
        logger.debug(
            f'using gsutil for source {source}, destination {destination_bucket}',
        )
        proc = subprocess.Popen(
            [
                'gsutil',
                '-m',
                'cp',
                '-r',
                os.path.join(self.output_dir, '*'),
                destination_bucket,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # I know, magic numbers
        completed = False
        for attempt in range(9):
            try:
                # Wait for 1 hour for the operation to complete
                _, err = proc.communicate(timeout=3600)
            except subprocess.TimeoutExpired:
                logger.warning(f'Attempt #{attempt+1} timed out!')
                continue
            except Exception as e:
                proc.kill()
                logger.error(f'There was a problem copying files to bucket {destination_bucket}: {e}')
                break
            else:
                completed = True
                source = Path(self.output_dir) / '*'
                logger.info(f'gsutil copy for source {source} destination {destination_bucket} COMPLETED!')
                break
        if not completed:
            proc.kill()
            _, err = proc.communicate()
            err_str = err.decode('utf-8')
            logger.error(f'COULD NOT COMPLETE file copy to GCP Bucket {destination_bucket}: {err_str}')

    @staticmethod
    def resource_for_stage(resource):
        """Build a resource stage description for the given information.

        :param resource: information to use for building the resource stage description
        :return: resource stage description
        """
        resource_stage = Dict()
        resource_stage.path = ''
        resource_stage.uri = resource.uri
        resource_stage.output_filename = os.path.basename(resource.uri)
        return resource_stage


class CustomSubProcError(Exception):
    """Custom subprocess exception class."""


def subproc(cmd: str, **kwargs) -> None:
    """Run a cmd as a subprocess.

    This catches errors that are 'raised' in the STDERR even if the command doesn't return a code > 0.

    Arguments:
        cmd -- command string to run

    Raises:
        CustomSubProcError
    """

    def raise_exception(sp: subprocess.CompletedProcess, error: str) -> None:
        raise CustomSubProcError(f'FAILED to run command {sp.args}, with return code {sp.returncode}, error: {error}')

    try:
        sp = subprocess.run(cmd, shell=True, text=True, capture_output=True, check=False, **kwargs)  # noqa: S602
        sp.check_returncode()
    except subprocess.CalledProcessError as err:
        raise_exception(sp=sp, error=err)
    error_keywords = ('error', 'killed')
    if any(e in sp.stderr.lower() for e in error_keywords):
        raise_exception(sp=sp, error=sp.stderr)

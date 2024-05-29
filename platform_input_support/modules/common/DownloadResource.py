import os
import logging
import datetime
import ftplib
from furl import furl
import subprocess
import urllib.request, urllib.parse, urllib.error
from platform_input_support.manifest import ManifestResource, ManifestStatus, get_manifest_service
# Common packages
from typing import Dict

logger = logging.getLogger(__name__)

class DownloadResource(object):
    """
    This class implements a URI download helper
    """

    def __init__(self, output_dir, manifest_service=None):
        """
        Constructor.

        :param output_dir: path to download destination folder
        """
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.output_dir = output_dir
        self.__manifest_service = manifest_service

    @property
    def manifest_service(self):
        if self.__manifest_service is None:
            self.__manifest_service = get_manifest_service()
        return self.__manifest_service

    def replace_suffix(self, args):
        if args.suffix:
            self.suffix = args.suffix

    def set_filename(self, filename) -> str:
        """
        Build final destination file path.

        :param filename: Base file name
        """
        return os.path.join(self.output_dir, filename.replace('{suffix}', self.suffix))

    def execute_download(self, resource_info, retry_count=3) -> ManifestResource:
        """
        Perform downloading of a resource described by the given resource information.

        :param resource_info: information on the resource to download
        :param retry_count: number of times to re-try downloading the resource in case of error, '1' by default
        :return: the download destination path when successful, empty path if not
        """
        # TODO - Change in return type breaks the unit test, although the return value wasn't used anywhere but in tests
        logger.debug("Start to download\n\t{} ".format(resource_info.uri))
        downloaded_resource = self.manifest_service.new_resource()
        downloaded_resource.source_url = resource_info.uri
        destination_filename = self.set_filename(resource_info.output_filename)
        downloaded_resource.path_destination = destination_filename
        errors = list()
        logger.info(f"[DOWNLOAD] BEGIN: '{resource_info.uri}' -> '{destination_filename}'")
        for attempt in range(retry_count):
            try:
                opener = urllib.request.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                if resource_info.accept:
                    opener.addheaders = [('User-agent', 'Mozilla/5.0'), ('Accept', resource_info.accept)]
                urllib.request.install_opener(opener)
                # WARNING - Funny thing is that some URLs won't give you an error, but random data
                urllib.request.urlretrieve(resource_info.uri, destination_filename)
            except urllib.error.URLError as e:
                try:
                    if 500 <= e.code < 600:
                        errors.append(f"[DOWNLOAD] ERROR: {e.reason}, status code {e.code}")
                        logger.error(errors[-1])
                        continue
                except AttributeError:
                    pass
                errors.append(f"[DOWNLOAD] ERROR: {e.reason}")
                logger.error(errors[-1])
                break
            except IOError as io_error:
                errors.append("IOError: {}".format(io_error))
                logger.error(errors[-1])
            except Exception as e:
                errors.append("Error: {}".format(e))
                logger.error(errors[-1])
            else:
                downloaded_resource.status_completion = ManifestStatus.COMPLETED
                downloaded_resource.msg_completion = f"Download completed after {attempt + 1} attempt(s)"
                logger.info(f"[DOWNLOAD] END, ({attempt + 1} attempt(s)): '{resource_info.uri}' -> '{destination_filename}'")
                break
        if downloaded_resource.status_completion == ManifestStatus.NOT_COMPLETED:
            downloaded_resource.status_completion = ManifestStatus.FAILED
            downloaded_resource.msg_completion = " -E- ".join(errors)
            logger.error(f"[DOWNLOAD] FAILED: '{resource_info.uri}' -> '{destination_filename}'")
        return downloaded_resource

    def ftp_download(
        self,
        resource_info: Dict,
        retry_count: int = 3,
        timeout: int = 3600
    ) -> ManifestResource:
        """
        Perform an FTP download

        :param resource_info: information on the resource to download
        :return: the download destination path when successful, empty path if not
        """
        # WARNING - TODO - resource_info.output_dir is NOT BEING used anywhere, it should be used instead of self.output_dir, if set.
        print("Start to download\n\t{uri} ".format(uri=resource_info.uri))
        filename = self.set_filename(resource_info.output_filename)
        downloaded_resource = self.manifest_service.new_resource()
        downloaded_resource.source_url = resource_info.uri
        downloaded_resource.path_destination = filename
        errors = list()
        logger.info(f"[FTP] BEGIN: '{resource_info.uri}' -> '{filename}'")
        url = furl(resource_info.uri)
        for attempt in range(retry_count):
            try:
                ftp = ftplib.FTP(str(url.host), timeout=timeout)
                ftp.login()
                with open(filename, "wb") as f:
                    ftp.retrbinary("RETR " + str(url.path), f.write)
                    ftp.quit()
            except ftplib.all_errors as e:
                errors.append(f"FAILED Attempt #{attempt + 1} to download '{resource_info.uri}', reason '{e}'")
                logger.warning(errors[-1])
            else:
                downloaded_resource.status_completion = ManifestStatus.COMPLETED
                downloaded_resource.msg_completion = f"Download completed after {attempt + 1} attempt(s)"
                break
        if downloaded_resource.status_completion == ManifestStatus.NOT_COMPLETED:
            logger.warning(f"[FTP] Re-trying with a command line tool - '{resource_info.uri}'")
            # EBI FTP started to reply ConnectionResetError: [Errno 104] Connection reset by peer.
            # I had an exchange of email with sysinfo, they suggested us to use wget.
            # WARNING - Magic Number timeout
            cmd = 'curl ' + resource_info.uri + ' --output ' + filename
            for attempt in range(retry_count):
                logger.warning(f"[FTP] Attempt #{attempt} Re-try Command '{cmd}'")
                # TODO We need to handle the completion of this command, I think it would be worth writing a handler helper
                try:
                    cmd_result = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout, check=True)
                except subprocess.CalledProcessError as e:
                    errors.append(
                        f"[FTP] Failed attempt #{attempt} to download '{resource_info.uri}' with command '{cmd}', "
                        f"due to '{e.stderr}'")
                    logger.warning(errors[-1])
                except subprocess.TimeoutExpired as e:
                    errors.append(
                        f"[FTP] Failed attempt #{attempt} to download '{resource_info.uri}' with command '{cmd}', "
                        f"due to time out for {timeout}s")
                    logger.warning(errors[-1])
                    timeout += int(timeout / 2)
                else:
                    downloaded_resource.status_completion = ManifestStatus.COMPLETED
                    downloaded_resource.msg_completion = f"Download completed after {attempt + 1} attempt(s)"
                    break
            if downloaded_resource.status_completion == ManifestStatus.NOT_COMPLETED:
                downloaded_resource.status_completion = ManifestStatus.FAILED
                downloaded_resource.msg_completion = " -E- ".join(errors)
                logger.error(f"[FTP] FAILED ({attempt + 1} attempt(s)): '{resource_info.uri}' -> '{filename}'")
            else:
                logger.info(f"[FTP] END ({attempt + 1} attempt(s)): '{resource_info.uri}' -> '{filename}'")
        return downloaded_resource

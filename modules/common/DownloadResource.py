import os
import logging
import datetime
import threading
import subprocess
import urllib.request, urllib.parse, urllib.error
from manifest import ManifestResource, ManifestStatus, get_manifest_service
# Common packages
from typing import Dict

logger = logging.getLogger(__name__)


# Decorator for the threading parameter.
# @deprecated(reason='This method is not being used anywhere in the code, '
#                  'multithreading when downloading data would need to be refactored to find out its best fit')
def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class DownloadResource(object):
    """
    This class implements a URI download helper
    """

    def __init__(self, output_dir):
        """
        Constructor.

        :param output_dir: path to download destination folder
        """
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.output_dir = output_dir

    def replace_suffix(self, args):
        if args.suffix:
            self.suffix = args.suffix

    def set_filename(self, filename) -> str:
        """
        Build final destination file path.

        :param filename: Base file name
        """
        return os.path.join(self.output_dir, filename.replace('{suffix}', self.suffix))

    def execute_download(self, resource_info, retry_count=1) -> ManifestResource:
        """
        Perform downloading of a resource described by the given resource information.

        :param resource_info: information on the resource to download
        :param retry_count: number of times to re-try downloading the resource in case of error, '1' by default
        :return: the download destination path when successful, empty path if not
        """
        # TODO - Change in return type breaks the unit test, although the return value wasn't used anywhere but in tests
        logger.debug("Start to download\n\t{} ".format(resource_info.uri))
        downloaded_resource = get_manifest_service().new_resource()
        downloaded_resource.source_url = resource_info.uri
        errors = list()
        for attempt in range(retry_count):
            try:
                opener = urllib.request.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                if resource_info.accept:
                    opener.addheaders = [('User-agent', 'Mozilla/5.0'), ('Accept', resource_info.accept)]
                urllib.request.install_opener(opener)
                destination_filename = self.set_filename(resource_info.output_filename)
                downloaded_resource.path_destination = destination_filename
                logger.info(f"[DOWNLOAD] BEGIN: '{resource_info.uri}' -> '{destination_filename}'")
                urllib.request.urlretrieve(resource_info.uri, destination_filename)
            except urllib.error.URLError as e:
                errors.append(f"[DOWNLOAD] ERROR: {e.reason}")
                logger.error(errors[-1])
                try:
                    # TODO - This is useful information to report back to the caller
                    if 500 <= e.code < 600:
                        continue
                    break
                except AttributeError:
                    pass
            except IOError as io_error:
                errors.append("IOError: {}".format(io_error))
                logger.error(errors[-1])
            except Exception as e:
                errors.append("Error: {}".format(e))
                logger.error(errors[-1])
            else:
                downloaded_resource.status_completion = ManifestStatus.COMPLETED
                downloaded_resource.msg_completion = "At least one download attempt finished with no errors"
                logger.info(f"[DOWNLOAD] END: '{resource_info.uri}' -> '{destination_filename}'")
        if downloaded_resource.status_completion == ManifestStatus.NOT_COMPLETED:
            downloaded_resource.status_completion = ManifestStatus.FAILED
            downloaded_resource.msg_completion = " -E- ".join(errors)
        return downloaded_resource

    # @deprecated(reason='no longer used, it would benefit from a refactoring round')
    @threaded
    def execute_download_threaded(self, resource_info):
        self.execute_download(resource_info)

    def ftp_download(self, resource_info: Dict) -> str:
        """
        Perform an FTP download

        :param resource_info: information on the resource to download
        :return: the download destination path when successful, empty path if not
        """
        print("Start to download\n\t{uri} ".format(uri=resource_info.uri))
        try:
            filename = self.set_filename(resource_info.output_filename)
            logger.info(f"[DOWNLOAD] BEGIN: '{resource_info.uri}' -> '{filename}'")
            urllib.request.urlretrieve(resource_info.uri, filename)
            urllib.request.urlcleanup()
            logger.info(f"[DOWNLOAD] END: '{resource_info.uri}' -> '{filename}'")
        except Exception:
            logger.warning("[DOWNLOAD] Re-trying with a command line tool - '{}'".format(resource_info.uri))
            # EBI FTP started to reply ConnectionResetError: [Errno 104] Connection reset by peer.
            # I had an exchange of email with sysinfo, they suggested us to use wget.
            cmd = 'curl ' + resource_info.uri + ' --output ' + filename
            logger.warning("[DOWNLOAD] Re-try Command '{}'".format(cmd))
            # TODO We need to handle the completion of this command, I think it would be worth writing a handler helper
            # TODO There is neither a timed wait nor a re-try strategy for this command
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        return filename

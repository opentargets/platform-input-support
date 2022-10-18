import os
import logging
import datetime
import threading
import subprocess
import urllib.request, urllib.parse, urllib.error
# Common packages
from typing import Dict
from modules.common.TqdmUpTo import TqdmUpTo

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

    def execute_download(self, resource_info, retry_count=1) -> str:
        """
        Perform downloading of a resource described by the given resource information.

        :param resource_info: information on the resource to download
        :param retry_count: number of times to re-try downloading the resource in case of error, '1' by default
        :return: the download destination path when successful, empty path if not
        """
        logger.debug("Start to download\n\t{} ".format(resource_info.uri))
        for attempt in range(retry_count):
            try:
                opener = urllib.request.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                if resource_info.accept:
                    opener.addheaders = [('User-agent', 'Mozilla/5.0'), ('Accept', resource_info.accept)]
                urllib.request.install_opener(opener)
                destination_filename = self.set_filename(resource_info.output_filename)
                logger.info(f"[DOWNLOAD] BEGIN: '{resource_info.uri}' -> '{destination_filename}'")
                urllib.request.urlretrieve(resource_info.uri, destination_filename)
                logger.info(f"[DOWNLOAD] END: '{resource_info.uri}' -> '{destination_filename}'")
                return destination_filename
            except urllib.error.URLError as e:
                logger.error('[DOWNLOAD] ERROR:', e.reason)
                try:
                    # TODO - This is useful information to report back to the caller
                    if 500 <= e.code < 600:
                        continue
                    break
                except AttributeError:
                    pass
            except IOError as io_error:
                logger.error("IOError: {}".format(io_error))
            except Exception as e:
                logger.error("Error: {}".format(e))
            break
        return ''

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

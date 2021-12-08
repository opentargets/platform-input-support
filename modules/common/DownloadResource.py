import datetime
import urllib.request, urllib.parse, urllib.error
import logging
import threading
import shutil
import subprocess

# Common packages
from typing import Dict

from modules.common.TqdmUpTo import TqdmUpTo


# Decorator for the threading parameter.
def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


logger = logging.getLogger(__name__)


# Generic class to download a specific URI
class DownloadResource(object):

    def __init__(self, output_dir):
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.output_dir = output_dir

    def replace_suffix(self, args):
        if args.suffix:
            self.suffix = args.suffix

    def set_filename(self, param_filename):
        return self.output_dir + '/' + param_filename.replace('{suffix}', self.suffix)

    def execute_download(self, resource_info, retry_count=1) -> str:
        logger.debug("Start to download\n\t{uri} ".format(uri=resource_info.uri))
        try:
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            if resource_info.accept:
                opener.addheaders = [('User-agent', 'Mozilla/5.0'), ('Accept', resource_info.accept)]
            urllib.request.install_opener(opener)
            destination_filename = self.set_filename(resource_info.output_filename)
            with TqdmUpTo(unit='B', unit_scale=True, miniters=1,
                          desc=resource_info.uri.split('/')[-1]) as t:  # all optional kwargs
                urllib.request.urlretrieve(resource_info.uri, destination_filename,
                                           reporthook=t.update_to, data=None)
            return destination_filename
        except urllib.error.URLError as e:
            logger.error('Download error:', e.reason)
            if retry_count > 0:
                if hasattr(e, 'code') and 500 <= e.code < 600:
                    return self.execute_download(resource_info, retry_count - 1)
        except IOError as io_error:
            logger.error("IOError: {io_error}".format(io_error=io_error))
            return None
        except Exception as e:
            logger.error("Error: {msg}".format(msg=e))
            return None

    @threaded
    def execute_download_threaded(self, resource_info):
        self.execute_download(resource_info)

    def ftp_download(self, resource_info: Dict) -> str:
        print("Start to download\n\t{uri} ".format(uri=resource_info.uri))
        try:
            filename = self.set_filename(resource_info.output_filename)
            urllib.request.urlretrieve(resource_info.uri, filename)
            urllib.request.urlcleanup()
        except Exception:
            logger.error("Warning: FTP! {file}".format(file=resource_info.uri))
            # try with wget temp solution
            cmd = 'curl ' + resource_info.uri + ' --output ' + filename
            logger.info("wget attempt {cmd}".format(cmd=cmd))
            subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        return filename

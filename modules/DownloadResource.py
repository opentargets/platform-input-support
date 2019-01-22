import datetime
import urllib
import threading

# Common packages
from modules.common.TqdmUpTo import TqdmUpTo

# Decorator for the threading parameter.
def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


# Generic class to download a specific URI
# TODO: execute_download requires a dict("uri","output_filename"). Add a function to check the input
class DownloadResource(object):

    def __init__(self, output_dir):
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.output_dir = output_dir

    def replace_suffix(self, args):
        if args.suffix:
            self.suffix = args.suffix

    def set_filename(self, param_filename):
        return self.output_dir+'/'+param_filename.replace('{suffix}', self.suffix)

    def execute_download(self, resource_info):
        print "Start to download\n\t{uri} data ".format(uri=resource_info.uri)
        try:
            download = urllib.URLopener()
            destination_filename = self.set_filename(resource_info.output_filename)
            with TqdmUpTo(unit='B', unit_scale=True, miniters=1,
                          desc=resource_info.uri.split('/')[-1]) as t:  # all optional kwargs
                download.retrieve(resource_info.uri, destination_filename,
                                  reporthook=t.update_to)
        except IOError as io_error:
            print "IOError: {io_error}".format(io_error=io_error)
        except Exception as e:
            print "Error: {msg}".format(msg=e)

        return destination_filename

    @threaded
    def execute_download_threaded(self, resource_info):
        self.execute_download(resource_info)

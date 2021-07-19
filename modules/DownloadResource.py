import datetime
import urllib.request, urllib.parse, urllib.error
from http import cookiejar
import requests
import threading
from ftplib import FTP
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

    def execute_download(self, resource_info, retry_count=1):
        print("Start to download\n\t{uri} ".format(uri=resource_info.uri))
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
        except IOError as io_error:
            print("IOError: {io_error}".format(io_error=io_error))
            return None
        except urllib.error.URLError as e:
            print('Download error:', e.reason)
            content = None
            if retry_count > 0:
                if hasattr(e, 'code') and 500 <= e.code < 600:
                    return self.execute_download(resource_info, retry_count-1)
        except Exception as e:
            print("Error: {msg}".format(msg=e))
            return None


        return destination_filename

    @threaded
    def execute_download_threaded(self, resource_info):
        self.execute_download(resource_info)

    def ftp_download(self, resource_info) -> str:
        print("Start to download\n\t{uri} ".format(uri=resource_info['uri']))
        filename = self.set_filename(resource_info['output_filename'])
        urllib.request.urlretrieve(resource_info['uri'], filename)
        urllib.request.urlcleanup()

        return filename

    def downloadHttp(self, resource_info, retry_count=3, proxy=None, data=None):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.100 Safari/537.36"
        }
        destination_filename = self.set_filename(resource_info.output_filename)
        if resource_info.uri is None:
            return None
        try:
            req = urllib.request.Request(resource_info.uri, headers=headers, data=data)
            cookie = cookiejar.CookieJar()
            cookie_process = urllib.request.HTTPCookieProcessor(cookie)
            opener = urllib.request.build_opener()
            if proxy:
                proxies = {urllib.urlparse(resource_info.uri).scheme: proxy}
                opener.add_handler(urllib.request.ProxyHandler(proxies))
            content = opener.open(req).read()
        except urllib.error.URLError as e:
            print('downloadHttp download error:', e.reason)
            content = None
            if retry_count > 0:
                if hasattr(e, 'code') and 500 <= e.code < 600:
                    return self.download(resource_info.uri, retry_count-1, headers, proxy, data)

        return content
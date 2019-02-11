import functools
from contextlib import contextmanager
import os, sys
import zipfile
import tempfile as tmp
import requests as r
import requests_file
import gzip
GZIP_MAGIC_NUMBER = "1f8b"
import logging

def is_gzip(filename):
    open_file = open(filename)
    return open_file.read(2).encode("hex") == GZIP_MAGIC_NUMBER


def get_lines(input_filename):
    i = 0
    if is_gzip(input_filename):
        with gzip.open(input_filename, 'rb') as f:
            for i, l in enumerate(f):
                pass
    return i+1


def get_output_dir(output_dir, default_output_dir):
    if output_dir is None:
        output_dir = default_output_dir
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    except OSError:
        sys.exit('Fatal: output directory "' + output_dir + '" does not exist and cannot be created')

    return output_dir


def make_zip(file_with_path):
    filename_zip = file_with_path+".zip"
    zf = zipfile.ZipFile(filename_zip, "w",zipfile.ZIP_DEFLATED, allowZip64 = True)
    zf.write(file_with_path)
    zf.close()
    return filename_zip

def urllify(string_name):
    """return a file:// urlified simple path to a file:// is :// is not contained in it"""
    return string_name if '://' in string_name else 'file://' + string_name


class URLZSource(object):
    def __init__(self, filename, *args, **kwargs):
        """Easy way to open multiple types of URL protocol (e.g. http:// and file://)
        as well as handling compressed content (e.g. .gz or .zip) if appropriate.

        Just in case you need to use proxies for url use it as normal
        named arguments to requests.

        >>> # proxies = {}
        >>> # if Config.HAS_PROXY:
        ...    # self.proxies = {"http": Config.PROXY,
        ...                      # "https": Config.PROXY}
        >>> # with URLZSource('http://var.foo/noname.csv',proxies=proxies).open() as f:

        """
        self.filename = urllify(filename)
        self.args = args
        self.kwargs = kwargs
        self.proxies = None
        self.r_session = r.Session()
        self.r_session.mount('file://', requests_file.FileAdapter())
        logging.debug(filename)

    @contextmanager
    def _open_local(self, filename, mode):
        """
        This is an internal function to handle opening the temporary file
        that the URL has been downloaded to, including handling compression
        if appropriate
        """
        open_f = None

        if filename.endswith('.gz'):
            open_f = functools.partial(gzip.open, mode='rb')

        elif filename.endswith('.zip'):
            zipped_data = zipfile.ZipFile(filename)
            info = zipped_data.getinfo(zipped_data.filelist[0].orig_filename)

            filename = info
            open_f = functools.partial(zipped_data.open)
        else:
            open_f = functools.partial(open, mode='r')

        with open_f(filename) as fd:
            yield fd

    @contextmanager
    def open(self, mode='r'):
        """
        This downloads the URL to a temporary file, naming the file
        based on the URL.
        """

        if self.filename.startswith('ftp://'):
            raise NotImplementedError('finish ftp')

        else:
            local_filename = self.filename.split('://')[-1].split('/')[-1]
            f = self.r_session.get(url=self.filename, stream=True, **self.kwargs)
            f.raise_for_status()
            file_to_open = None
            #this has to be "delete=false" so that it can be re-opened with the same filename
            #to be read out again
            with tmp.NamedTemporaryFile(mode='wb', suffix=local_filename, delete=False) as fd:
                # write data into file in streaming fashion
                file_to_open = fd.name
                for block in f.iter_content(1024):
                    fd.write(block)

            with self._open_local(file_to_open, mode) as fd:
                yield fd

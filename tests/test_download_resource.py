import mock
import unittest
from modules.DownloadResource import DownloadResource
from definitions import PIS_OUTPUT_ANNOTATIONS
from addict import Dict
import re

class DownloadResourceTests(unittest.TestCase):
    def setUp(self):
        self.resource_info = Dict()
        self.resource_info.uri = "https://google.com"
        self.resource_info.output_filename = "resource-{suffix}.txt"

    @mock.patch('urllib.URLopener')
    def test_execute_download(self, urlopen_mock):
        conn = mock.Mock()
        conn.read.return_value = 'byte'
        urlopen_mock.return_value = conn
        _download_resource = DownloadResource(PIS_OUTPUT_ANNOTATIONS)
        destination_filename = _download_resource.execute_download(self.resource_info)
        assert re.search('([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))', destination_filename)

    

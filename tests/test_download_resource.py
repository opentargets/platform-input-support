import mock
import unittest
from addict import Dict
from munch import Munch
from manifest import get_manifest_service
from definitions import PIS_OUTPUT_DIR
from modules.common.DownloadResource import DownloadResource
import re


class DownloadResourceTests(unittest.TestCase):
    def setUp(self):
        self.resource_info = Dict()
        self.resource_info.uri = "https://google.com"
        self.resource_info.output_filename = "resource-{suffix}.txt"
        # Manifest subsystem configuration mock-up
        _ = get_manifest_service(
            args=Munch.fromDict({"gcp_bucket": None}),
            configuration=Munch.fromDict(
                {
                    "config": {"manifest": {"file_name": "manifest.json"}},
                    "output_dir": "/tmp",
                }
            ),
            force_new=True,
        )

    @mock.patch("urllib.request")
    def test_execute_download(self, urlopen_mock):
        _download_resource = DownloadResource(PIS_OUTPUT_DIR)
        download_manifest = _download_resource.execute_download(self.resource_info)
        assert re.search(
            "([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))",
            download_manifest.path_destination,
        )

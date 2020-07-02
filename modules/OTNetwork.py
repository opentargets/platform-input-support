from definitions import PIS_OUTPUT_OTNETWORK, PIS_OUTPUT_ANNOTATIONS
from DownloadResource import DownloadResource
import datetime
import logging


logger = logging.getLogger(__name__)


class OTNetwork(object):

    def __init__(self, yaml_dict):
        self.intact_info = yaml_dict.intact_info
        self.gs_output_dir = yaml_dict.gs_output_dir


    def download_intact_file(self):
        download = DownloadResource(PIS_OUTPUT_ANNOTATIONS)
        return download.ftp_download(self.intact_info)

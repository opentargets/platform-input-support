from definitions import PIS_OUTPUT_INTERACTIONS
from .DownloadResource import DownloadResource
from .EnsemblResource import EnsemblResource
from .SparkHelpers import SparkHelpers
from .common import make_ungzip, get_output_spark_files
import logging
import os

logger = logging.getLogger(__name__)

class Interactions(object):

    def __init__(self, yaml_dict):
        self.yaml =  yaml_dict
        self.gs_output_dir = yaml_dict.gs_output_dir
        self.list_files_downloaded = {}
        self.download = DownloadResource(PIS_OUTPUT_INTERACTIONS)

    def get_rna_central(self):
        return self.download.ftp_download(self.yaml.rna_central)


    def get_intact_info_file(self):
        return self.download.ftp_download(self.yaml.intact_info)

    def get_uniprot_info_file(self):
        return self.download.ftp_download(self.yaml.uniprot_info)

    def getIntactResources(self):
        intact_info_filename = self.get_intact_info_file()
        self.list_files_downloaded[intact_info_filename] = {'resource': self.yaml.intact_info.resource,
                                                            'gs_output_dir': self.gs_output_dir }
        rna_file=self.get_rna_central()
        self.list_files_downloaded[rna_file] = {'resource': self.yaml.rna_central.resource,
                                                          'gs_output_dir': self.gs_output_dir }
        uniprot=self.get_uniprot_info_file()
        self.list_files_downloaded[uniprot] = {'resource': self.yaml.uniprot_info.resource,
                                                          'gs_output_dir': self.gs_output_dir }

        return self.list_files_downloaded
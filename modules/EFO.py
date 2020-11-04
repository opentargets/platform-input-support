import datetime
import logging
from definitions import PIS_OUTPUT_EFO, PIS_OUTPUT_ANNOTATIONS
from .DownloadResource import DownloadResource

logger = logging.getLogger(__name__)


class EFO(object):

    def __init__(self, yaml):
        self.yaml = yaml
        self.output_dir = PIS_OUTPUT_ANNOTATIONS
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.list_files_downloaded = {}


    def download_disease_phenotypes(self):
        print("disease phenotype")
        for entry in self.yaml.disease_phenotypes_downloads:
            download = DownloadResource(PIS_OUTPUT_ANNOTATIONS)
            destination_filename = download.execute_download(entry)
            self.list_files_downloaded[destination_filename] = {'resource': entry.resource,
                                                                'gs_output_dir': self.yaml.gs_output_dir}

    def download_efo_slim(self):
        for entry in self.yaml.efo_downloads:
            download = DownloadResource(PIS_OUTPUT_EFO)
            destination_filename = download.execute_download(entry)
            self.list_files_downloaded[destination_filename] = {'resource': entry.resource,
                                                                'gs_output_dir': self.yaml.gs_output_dir}

    def generate_efo(self):
        logger.info("EFO process")
        self.download_disease_phenotypes()
        self.download_efo_slim()
        return self.list_files_downloaded



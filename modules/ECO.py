import logging
from definitions import PIS_OUTPUT_ANNOTATIONS, PIS_OUTPUT_EFO
from .DownloadResource import DownloadResource
from .common.Riot import Riot

logger = logging.getLogger(__name__)


class ECO(object):

    def __init__(self, yaml, yaml_config):
        self.yaml = yaml
        self.local_output_dir = PIS_OUTPUT_ANNOTATIONS
        self.output_dir = yaml.gs_output_dir
        self.gs_save_json_dir = yaml.gs_output_dir + '/eco_json'
        self.list_files_downloaded = {}
        self.riot = Riot()


    def download_file(self, entry):
        download = DownloadResource(self.local_output_dir)
        destination_filename = download.execute_download(entry)
        self.list_files_downloaded[destination_filename] = {'resource': entry.resource,
                                                            'gs_output_dir': self.output_dir}
        return destination_filename

    def download_eco(self):
        for entry in self.yaml.eco_downloads:
            download = DownloadResource(self.local_output_dir)
            destination_filename = download.execute_download(entry)
            self.list_files_downloaded[destination_filename] = {'resource': entry.resource,
                                                                'gs_output_dir': self.output_dir}
            json_filename = self.riot.convert_owl_to_jsonld(destination_filename, self.local_output_dir, entry.owl_jq)
            self.list_files_downloaded[json_filename] = {'resource': None,
                                                         'gs_output_dir': self.gs_save_json_dir}

        return self.list_files_downloaded





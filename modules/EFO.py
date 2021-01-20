import logging
from addict import Dict
from definitions import PIS_OUTPUT_EFO, PIS_OUTPUT_ANNOTATIONS
from .DownloadResource import DownloadResource
from .helpers.EFO import EFO as Disease
from .helpers.HPOPhenotypes import HPOPhenotypes
from .helpers.HPO import HPO
from .helpers.MONDO import MONDO
from .common.Riot import Riot

logger = logging.getLogger(__name__)


class EFO(object):

    def __init__(self, yaml, yaml_config):
        self.yaml = yaml
        self.local_output_dir = PIS_OUTPUT_ANNOTATIONS
        self.output_dir = yaml.gs_output_dir
        self.gs_save_json_dir = yaml.gs_output_dir + '/efo_json'
        self.list_files_downloaded = {}
        self.riot = Riot(yaml_config)

    def download_file(self, entry):
        download = DownloadResource(self.local_output_dir)
        destination_filename = download.execute_download(entry)
        self.list_files_downloaded[destination_filename] = {'resource': entry.resource,
                                                            'gs_output_dir': self.output_dir}
        return destination_filename

    # as_original
    def download_file_original(self, uri):
        entry = Dict()
        entry.uri = uri
        entry.output_filename = uri[uri.rfind("/") + 1:]
        download = DownloadResource(self.local_output_dir)
        destination_filename = download.execute_download(entry)

        return destination_filename

    def download_extra_files(self,yaml):
        for entry in yaml:
            download = DownloadResource(self.local_output_dir)
            destination_filename = download.execute_download(entry)
            self.list_files_downloaded[destination_filename] = {'resource': entry.resource,
                                                                'gs_output_dir': self.output_dir}
        return destination_filename

    def download_owl_and_json(self, yaml_info):
        downloaded_file= self.download_file_original(yaml_info.uri)
        self.list_files_downloaded[downloaded_file] = {'resource': yaml_info.resource,
                                                       'gs_output_dir': self.output_dir}

        json_filename = self.riot.convert_owl_to_jsonld(downloaded_file, self.local_output_dir, yaml_info.owl_jq)
        self.list_files_downloaded[json_filename] = {'resource': None,
                                                     'gs_output_dir': self.gs_save_json_dir}

        return json_filename

    def generate_efo(self):
        logger.info("Running EFO step ")
        #Potentially obsolete soon!
        self.download_extra_files(self.yaml.efo_extra_downloads)

        hpo_pheno_filename = self.download_file_original(self.yaml.hpo_phenotypes.uri)
        self.list_files_downloaded[hpo_pheno_filename] = {'resource': None,
                                                         'gs_output_dir': self.output_dir}

        hpo_phenotypes = HPOPhenotypes(hpo_pheno_filename)
        hpo_phenotypes.run(self.yaml.hpo_phenotypes.output_filename)

        mondo_filename = self.download_owl_and_json(self.yaml.disease.mondo)
        mondo = MONDO(mondo_filename)
        mondo.generate()
        mondo.save_mondo(self.yaml.disease.mondo.output_filename)

        efo_filename = self.download_owl_and_json(self.yaml.disease.efo)
        diseases = Disease(efo_filename)
        diseases.generate()
        diseases.create_paths()
        diseases.save_static_therapeuticarea_file(self.yaml.disease.efo.static.therapeutic_area)
        diseases.save_static_disease_file(self.yaml.disease.efo.static.diseases)
        diseases.save_diseases(self.yaml.disease.efo.output_filename)


        hpo_filename = self.download_owl_and_json(self.yaml.disease.hpo)
        hpo = HPO(hpo_filename)
        hpo.generate()
        hpo.save_hpo(self.yaml.disease.hpo.output_filename)

        return self.list_files_downloaded



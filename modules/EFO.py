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
        # Legacy between data_pipeline and ETL. TODO: remove legacy datapipeline
        self.gs_save_json_dir = yaml.gs_output_dir + '/efo_json'
        self.list_files_downloaded = {}
        self.riot = Riot(yaml_config)


    def download_file(self, entry):
        download = DownloadResource(self.local_output_dir)
        destination_filename = download.execute_download(entry)
        self.list_files_downloaded[destination_filename] = {'resource': entry.resource,
                                                            'gs_output_dir': self.output_dir}
        return destination_filename

    # Download with the same original name
    def download_file_original(self, uri):
        entry = Dict()
        entry.uri = uri
        entry.output_filename = uri[uri.rfind("/") + 1:]
        download = DownloadResource(self.local_output_dir)
        destination_filename = download.execute_download(entry)

        return destination_filename

    # This method will be soon obsolete. Legacy with data_pipeline
    def download_extra_files(self,yaml):
        for entry in yaml:
            download = DownloadResource(self.local_output_dir)
            destination_filename = download.execute_download(entry)
            self.list_files_downloaded[destination_filename] = {'resource': entry.resource,
                                                                'gs_output_dir': self.output_dir}
        return destination_filename

    # This method download and convert the owl file into JSON using riot.
    # More details in the README
    def download_owl_and_json(self, yaml_info):
        downloaded_file= self.download_file_original(yaml_info.uri)
        self.list_files_downloaded[downloaded_file] = {'resource': yaml_info.resource,
                                                       'gs_output_dir': self.output_dir}

        #downloaded_file="/Users/cinzia/gitRepositories/platform-input-support/output/annotation-files/efo/efo_otar_slim.owl"
        json_filename = self.riot.convert_owl_to_jsonld(downloaded_file, self.local_output_dir, yaml_info.owl_jq)
        #json_filename = "/Users/cinzia/data/final.json"
        return json_filename

    # Download phenotype.hpoa and create a JSON output with a subset of info.
    def get_hpo_phenotype(self):
        hpo_pheno_filename = self.download_file_original(self.yaml.hpo_phenotypes.uri)
        hpo_phenotypes = HPOPhenotypes(hpo_pheno_filename)
        hpo_filename = hpo_phenotypes.run(self.yaml.hpo_phenotypes.output_filename)
        self.list_files_downloaded[hpo_filename] = {'resource': 'ontology-hpoa',
                                                    'gs_output_dir': self.gs_save_json_dir}


    # Download hp.owl and create a JSON output with a subset of info.
    def get_ontology_hpo(self):
        hpo_filename = self.download_owl_and_json(self.yaml.disease.hpo)
        hpo = HPO(hpo_filename)
        hpo.generate()
        hpo_filename = hpo.save_hpo(self.yaml.disease.hpo.output_filename)
        self.list_files_downloaded[hpo_filename] = {'resource': self.yaml.disease.hpo.resource+"-etl",
                                                    'gs_output_dir': self.gs_save_json_dir}


    # Download mondo.owl and create a JSON output with a subset of info.
    def get_ontology_mondo(self):
        mondo_filename = self.download_owl_and_json(self.yaml.disease.mondo)
        mondo = MONDO(mondo_filename)
        mondo.generate()
        filename=mondo.save_mondo(self.yaml.disease.mondo.output_filename)
        self.list_files_downloaded[filename] = {'resource': self.yaml.disease.mondo.resource+"-etl",
                                                    'gs_output_dir': self.gs_save_json_dir}

    # Download efo_otar_slim.owl and create a JSON output with a subset of info.
    def get_ontology_EFO(self):
        efo_filename = self.download_owl_and_json(self.yaml.disease.efo)
        diseases = Disease(efo_filename)
        diseases.generate()
        diseases.create_paths()
        diseases.save_static_disease_file(self.yaml.disease.efo.static.diseases)
        disease_filename = diseases.save_diseases(self.yaml.disease.efo.output_filename)
        self.list_files_downloaded[disease_filename] = {'resource': self.yaml.disease.efo.resource+"-etl",
                                                        'gs_output_dir': self.gs_save_json_dir}


    def generate_efo(self):
        logger.info("Running EFO step ")
        #Potentially obsolete soon! Legacy data_pipeline : TODO remove legacy
        #self.download_extra_files(self.yaml.efo_extra_downloads)

        # Generate the ontologies and the phenotype mapping file.
        #self.get_hpo_phenotype()
        #self.get_ontology_mondo()
        #self.get_ontology_hpo()
        self.get_ontology_EFO()

        return self.list_files_downloaded

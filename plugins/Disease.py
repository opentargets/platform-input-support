import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads
from modules.common import create_folder
from modules.common.Riot import Riot
from plugins.helpers.EFO import EFO as EFO
from plugins.helpers.HPOPhenotypes import HPOPhenotypes
from plugins.helpers.HPO import HPO
from plugins.helpers.MONDO import MONDO

logger = logging.getLogger(__name__)

"""

"""


class Disease(IPlugin):
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def owl_to_json(self, filename_input, output_dir, resource, riot):
        file_ouput_path = output_dir + "/" + resource.path
        create_folder(file_ouput_path)
        return riot.convert_owl_to_jsonld(filename_input, file_ouput_path, resource.owl_jq)

    def download_converted_file(self, resource, output, riot):
        filename_input = Downloads.download_staging_http(output.staging_dir, resource)
        return self.owl_to_json(filename_input, output.staging_dir, resource, riot)

    def get_hpo_phenotypes(self, conf, output):
        hpo_pheno_filename = Downloads.download_staging_http(output.staging_dir, conf.etl.hpo_phenotypes)
        hpo_phenotypes = HPOPhenotypes(hpo_pheno_filename)
        create_folder(output.prod_dir + "/" + conf.etl.hpo_phenotypes.path)
        hpo_phenotypes.run(output.prod_dir + "/" + conf.etl.hpo_phenotypes.path + "/" + conf.etl.hpo_phenotypes.output_filename)

    def get_ontology_hpo(self, conf, output, riot):
        hpo_filename = self.download_converted_file(conf.etl.hpo, output, riot)
        hpo = HPO(hpo_filename)
        hpo.generate()
        create_folder(output.prod_dir + "/" + conf.etl.hpo.path)
        hpo.save_hpo(output.prod_dir + "/" + conf.etl.hpo.path + "/" + conf.etl.hpo.output_filename)

    # Download mondo.owl and create a JSON output with a subset of info.
    def get_ontology_mondo(self, conf, output, riot):
        mondo_filename = self.download_converted_file(conf.etl.mondo, output, riot)
        mondo = MONDO(mondo_filename)
        mondo.generate()
        create_folder(output.prod_dir + "/" + conf.etl.mondo.path)
        mondo.save_mondo(output.prod_dir + "/" + conf.etl.mondo.path + "/" + conf.etl.mondo.output_filename)

    def get_ontology_EFO(self, conf, output, riot):
        efo_filename = self.download_converted_file(conf.etl.efo, output, riot)
        efo = EFO(efo_filename)
        efo.generate()
        create_folder(output.prod_dir + "/" + conf.etl.efo.path)
        efo.save_static_disease_file(output.prod_dir + "/" + conf.etl.efo.path + "/" + conf.etl.efo.diseases_static_file)
        efo.save_diseases(output.prod_dir + "/" + conf.etl.efo.path + "/" + conf.etl.efo.output_filename)

    def process(self, conf, output, cmd_conf):
        riot = Riot(cmd_conf)
        self.get_ontology_EFO(conf, output, riot)
        self.get_ontology_mondo(conf, output, riot)
        self.get_ontology_hpo(conf, output, riot)
        self.get_hpo_phenotypes(conf, output)

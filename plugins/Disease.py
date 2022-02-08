import os
import logging
from yapsy.IPlugin import IPlugin
from plugins.helpers.HPO import HPO
from modules.common.Riot import Riot
from plugins.helpers.MONDO import MONDO
from modules.common import create_folder
from plugins.helpers.EFO import EFO as EFO
from modules.common.Downloads import Downloads
from plugins.helpers.HPOPhenotypes import HPOPhenotypes

logger = logging.getLogger(__name__)


class Disease(IPlugin):
    """
    Disease data collection step implementation
    """

    def __init__(self):
        """
        Constructor, prepare the logging subsystem
        """
        self._logger = logging.getLogger(__name__)

    def owl_to_json(self, filename_input, output_dir, resource, riot):
        """
        Convert OWL to JSON using RIOT and filter the result according to the given JQ filtering string

        :param filename_input: input file path with OWL content
        :param output_dir: output folder for JSON converted OWL format
        :param resource: information object with JQ filtering string information
        :return: destination file path of the conversion + filtering process
        """
        file_ouput_path = os.path.join(output_dir, resource.path)
        create_folder(file_ouput_path)
        return riot.convert_owl_to_jsonld(filename_input, file_ouput_path, resource.owl_jq)

    def download_and_convert_file(self, resource, output, riot):
        """
        Download, convert and filter the given ontology file into the specified output folder

        :param resource: resource information object to download with filtering information
        :param output: output folder for the converted + filtered data
        :param riot: Apache RIOT helper
        :return: destination file path for the converted + filtered data
        """
        return self.owl_to_json(Downloads.download_staging_http(output.staging_dir, resource),
                                output.staging_dir, resource, riot)

    def get_hpo_phenotypes(self, conf, output):
        """
        Collect and process HPO Phenotypes data into the given output folder

        :param conf: HPO phenotypes information for collection and processing
        :param output: output folder
        :return: destination file path for the processed collected information
        """
        create_folder(os.path.join(output.prod_dir, conf.etl.hpo_phenotypes.path))
        return HPOPhenotypes(Downloads.download_staging_http(output.staging_dir, conf.etl.hpo_phenotypes)) \
            .run(os.path.join(output.prod_dir, conf.etl.hpo_phenotypes.path, conf.etl.hpo_phenotypes.output_filename))

    def get_ontology_hpo(self, conf, output, riot):
        """
        Collect and process HPO ontology into the specified destination path

        :param conf: HPO ontology information for collection and processing
        :param output: output folder
        :param riot: Apache RIOT helper
        :return: destination file path for HPO collected and processed data
        """
        create_folder(os.path.join(output.prod_dir, conf.etl.hpo.path))
        hpo = HPO(self.download_and_convert_file(conf.etl.hpo, output, riot))
        hpo.generate()
        return hpo.save_hpo(os.path.join(output.prod_dir, conf.etl.hpo.path, conf.etl.hpo.output_filename))

    # Download mondo.owl and create a JSON output with a subset of info.
    def get_ontology_mondo(self, conf, output, riot):
        """
        Collect and process MONDO data into the specified destination path

        :param conf: MONDO information for collection and processing
        :param output: output folder
        :param riot: Apache RIOT helper
        :return: destination file path for MONDO collected and processed data
        """
        create_folder(os.path.join(output.prod_dir, conf.etl.mondo.path))
        mondo = MONDO(self.download_and_convert_file(conf.etl.mondo, output, riot))
        mondo.generate()
        return mondo.save_mondo(os.path.join(output.prod_dir, conf.etl.mondo.path, conf.etl.mondo.output_filename))

    def get_ontology_EFO(self, conf, output, riot):
        """
        Collect and process EFO ontology data into the specified destination path

        :param conf: EFO ontology for collection and processing
        :param output: output folder
        :param riot: Apache RIOT helper
        :return: destination file path for EFO ontology collected and processed data
        """
        create_folder(os.path.join(output.prod_dir, conf.etl.efo.path))
        efo = EFO(self.download_and_convert_file(conf.etl.efo, output, riot))
        efo.generate()
        efo.save_static_disease_file(os.path.join(output.prod_dir,
                                                  conf.etl.efo.path,
                                                  conf.etl.efo.diseases_static_file))
        return efo.save_diseases(os.path.join(output.prod_dir, conf.etl.efo.path, conf.etl.efo.output_filename))

    def process(self, conf, output, cmd_conf):
        """
        Disease pipeline step implementation, it collects and pre-processes EFO, MONDO, HPO and HPO phenotypes data

        :param conf: step configuration
        :param output: output folder for collected and pre-processed data
        :param cmd_conf: command line tools configuration
        """
        riot = Riot(cmd_conf)
        self.get_ontology_EFO(conf, output, riot)
        self.get_ontology_mondo(conf, output, riot)
        self.get_ontology_hpo(conf, output, riot)
        self.get_hpo_phenotypes(conf, output)

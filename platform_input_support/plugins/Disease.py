import os
import logging
from typing import List

from yapsy.IPlugin import IPlugin
from platform_input_support.plugins.helpers.HPO import HPO
from platform_input_support.modules.common.Riot import Riot
from platform_input_support.plugins.helpers.MONDO import MONDO
from platform_input_support.modules.common import create_folder
from platform_input_support.plugins.helpers.EFO import EFO
from platform_input_support.modules.common.Downloads import Downloads
from platform_input_support.plugins.helpers.HPOPhenotypes import HPOPhenotypes
from platform_input_support.manifest import ManifestResource, ManifestStatus, get_manifest_service

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
        self.step_name = "Disease"

    def owl_to_json(self, filename_input, output_dir, resource, riot):
        """
        Convert OWL to JSON using RIOT and filter the result according to the given JQ filtering string

        :param filename_input: input file path with OWL content
        :param output_dir: output folder for JSON converted OWL format
        :param resource: information object with JQ filtering string information
        :return: destination file path of the conversion + filtering process
        """
        file_output_path = os.path.join(output_dir, resource.path)
        logger.debug("OWL to JSON output path '{}'".format(file_output_path))
        create_folder(file_output_path)
        return riot.convert_owl_to_jsonld(filename_input, file_output_path, resource.owl_jq)

    def download_and_convert_file(self, resource, output, riot) -> ManifestResource:
        """
        Download, convert and filter the given ontology file into the specified output folder

        :param resource: resource information object to download with filtering information
        :param output: output folder for the converted + filtered data
        :param riot: Apache RIOT helper
        :return: destination file path for the converted + filtered data
        """
        download_manifest = Downloads.download_staging_http(output.staging_dir, resource)
        try:
            download_manifest.path_destination = self.owl_to_json(download_manifest.path_destination,
                                    output.staging_dir, resource, riot)
        except Exception as e:
            download_manifest.status_completion = ManifestStatus.FAILED
            download_manifest.msg_completion = str(e)
        else:
            download_manifest.msg_completion = f"OWL to JSON + JQ filtering with '{resource.owl_jq}'"
            download_manifest.status_completion = ManifestStatus.COMPLETED
        return download_manifest

    def get_hpo_phenotypes(self, conf, output) -> ManifestResource:
        """
        Collect and process HPO Phenotypes data into the given output folder

        :param conf: HPO phenotypes information for collection and processing
        :param output: output folder
        :return: destination file path for the processed collected information
        """
        create_folder(os.path.join(output.prod_dir, conf.etl.hpo_phenotypes.path))
        download_manifest = Downloads.download_staging_http(output.staging_dir, conf.etl.hpo_phenotypes)
        if download_manifest.status_completion == ManifestStatus.COMPLETED:
            hpo_phenotypes = HPOPhenotypes(download_manifest.path_destination)
            try:
                download_manifest.path_destination = hpo_phenotypes.run(
                    os.path.join(output.prod_dir,
                                 conf.etl.hpo_phenotypes.path,
                                 conf.etl.hpo_phenotypes.output_filename)
                )
            except Exception as e:
                download_manifest.msg_completion = f"COULD NOT produce HPO Phenotypes data due to '{e}'"
                download_manifest.status_completion = ManifestStatus.FAILED
            else:
                download_manifest.msg_completion = "Resulting dataset from HPO Phenotypes data"
                download_manifest.status_completion = ManifestStatus.COMPLETED
        return download_manifest

    def get_ontology_hpo(self, conf, output, riot) -> ManifestResource:
        """
        Collect and process HPO ontology into the specified destination path

        :param conf: HPO ontology information for collection and processing
        :param output: output folder
        :param riot: Apache RIOT helper
        :return: destination file path for HPO collected and processed data
        """
        create_folder(os.path.join(output.prod_dir, conf.etl.hpo.path))
        conversion_manifest = self.download_and_convert_file(conf.etl.hpo, output, riot)
        if conversion_manifest.status_completion == ManifestStatus.COMPLETED:
            hpo = HPO(conversion_manifest.path_destination)
            try:
                hpo.generate()
            except Exception as e:
                conversion_manifest.msg_completion = f"COULD NOT produce HPO dataset due to '{e}'"
                conversion_manifest.status_completion = ManifestStatus.FAILED
            else:
                conversion_manifest.path_destination = os.path.join(output.prod_dir,
                                                                conf.etl.hpo.path,
                                                                conf.etl.hpo.output_filename)
                try:
                    hpo.save_hpo(conversion_manifest.path_destination)
                except Exception as e:
                    conversion_manifest.msg_completion = f"COULD NOT produce HPO dataset due to '{e}'"
                    conversion_manifest.status_completion = ManifestStatus.FAILED
                else:
                    conversion_manifest.status_completion = ManifestStatus.COMPLETED
                    conversion_manifest.msg_completion = "HPO processed data source"
        return conversion_manifest

    # Download mondo.owl and create a JSON output with a subset of info.
    def get_ontology_mondo(self, conf, output, riot) -> ManifestResource:
        """
        Collect and process MONDO data into the specified destination path

        :param conf: MONDO information for collection and processing
        :param output: output folder
        :param riot: Apache RIOT helper
        :return: destination file path for MONDO collected and processed data
        """
        create_folder(os.path.join(output.prod_dir, conf.etl.mondo.path))
        conversion_manifest = self.download_and_convert_file(conf.etl.mondo, output, riot)
        if conversion_manifest.status_completion == ManifestStatus.COMPLETED:
            mondo = MONDO(conversion_manifest.path_destination)
            try:
                mondo.generate()
            except Exception as e:
                conversion_manifest.msg_completion = f"Unable to produce MONDO dataset due to '{e}'"
                conversion_manifest.status_completion = ManifestStatus.FAILED
            else:
                conversion_manifest.path_destination = os.path.join(output.prod_dir,
                                                                    conf.etl.mondo.path,
                                                                    conf.etl.mondo.output_filename)
                try:
                    mondo.save_mondo(conversion_manifest.path_destination)
                except Exception as e:
                    conversion_manifest.msg_completion = f"Unable to produce MONDO dataset due to '{e}'"
                    conversion_manifest.status_completion = ManifestStatus.FAILED
                else:
                    conversion_manifest.status_completion = ManifestStatus.COMPLETED
                    conversion_manifest.msg_completion = f"MONDO processed data source, JQ filter '{conf.etl.mondo.owl_jq}'"
        return conversion_manifest

    def get_ontology_EFO(self, conf, output, riot) -> List[ManifestResource]:
        """
        Collect and process EFO ontology data into the specified destination path

        :param conf: EFO ontology for collection and processing
        :param output: output folder
        :param riot: Apache RIOT helper
        :return: destination file path for EFO ontology collected and processed data
        """
        create_folder(os.path.join(output.prod_dir, conf.etl.efo.path))
        conversion_manifest = self.download_and_convert_file(conf.etl.efo, output, riot)
        static_disease_manifest = get_manifest_service().clone_resource(conversion_manifest)
        static_disease_manifest.path_destination = os.path.join(output.prod_dir,
                                                  conf.etl.efo.path,
                                                  conf.etl.efo.diseases_static_file)
        if conversion_manifest.status_completion == ManifestStatus.COMPLETED:
            efo = EFO(conversion_manifest.path_destination, conf=conf.etl.efo)
            try:
                efo.generate()
            except Exception as e:
                static_disease_manifest.msg_completion = f"Unable to produce the static disease file due to '{e}', Exception of type -> '{type(e)}'"
                self._logger.error(static_disease_manifest.msg_completion)
                static_disease_manifest.status_completion = ManifestStatus.FAILED
            else:
                try:
                    efo.save_static_disease_file(static_disease_manifest.path_destination)
                except Exception as e:
                    static_disease_manifest.msg_completion = f"Unable to produce the static disease file due to '{e}'"
                    self._logger.error(static_disease_manifest.msg_completion)
                    static_disease_manifest.status_completion = ManifestStatus.FAILED
                else:
                    static_disease_manifest.msg_completion += \
                        " and then processed by the pipeline into the resulting static disease dataset"
                    conversion_manifest.path_destination = \
                        os.path.join(output.prod_dir, conf.etl.efo.path, conf.etl.efo.output_filename)
                    try:
                        efo.save_diseases(conversion_manifest.path_destination)
                    except Exception as e:
                        static_disease_manifest.msg_completion = f"Unable to produce the static disease file due to '{e}'"
                        self._logger.error(static_disease_manifest.msg_completion)
                        static_disease_manifest.status_completion = ManifestStatus.FAILED
                    else:
                        conversion_manifest.msg_completion += \
                            " and some processing via EFO helper to produce this resulting diseases dataset"
        else:
            static_disease_manifest.msg_completion = f"FAILED due to an error converting and processing source file"
        return [conversion_manifest, static_disease_manifest]

    def process(self, conf, output, cmd_conf):
        """
        Disease pipeline step implementation, it collects and pre-processes EFO, MONDO, HPO and HPO phenotypes data

        :param conf: step configuration
        :param output: output folder for collected and pre-processed data
        :param cmd_conf: command line tools configuration
        """
        self._logger.info("[STEP] BEGIN, Disease")
        riot = Riot(cmd_conf)
        manifest_step = get_manifest_service().get_step(self.step_name)
        # TODO - Should I halt the step as soon as I face the first problem?
        manifest_step.resources.extend(self.get_ontology_EFO(conf, output, riot))
        manifest_step.resources.append(self.get_ontology_mondo(conf, output, riot))
        manifest_step.resources.append(self.get_ontology_hpo(conf, output, riot))
        manifest_step.resources.append(self.get_hpo_phenotypes(conf, output))
        # We try to compute checksums for whatever was collected
        get_manifest_service().compute_checksums(manifest_step.resources)
        if not get_manifest_service().are_all_resources_complete(manifest_step.resources):
            manifest_step.status_completion = ManifestStatus.FAILED
            manifest_step.msg_completion = "COULD NOT retrieve all the resources"
        # TODO - Validation
        if manifest_step.status_completion != ManifestStatus.FAILED:
            manifest_step.status_completion = ManifestStatus.COMPLETED
            manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, Disease")

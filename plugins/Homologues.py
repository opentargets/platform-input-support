import os
import errno
import logging
import subprocess
from typing import List

from addict import Dict
from yapsy.IPlugin import IPlugin
from modules.common.Utils import Utils
from modules.common import create_folder
from modules.common.DownloadResource import DownloadResource
from manifest import ManifestResource, ManifestStatus, get_manifest_service

logger = logging.getLogger(__name__)


class Homologues(IPlugin):
    """
    Class to download resources from Ensembl FTP for use in ETL target step (specifically to generate homologues).

    Takes the `homology` section of the `config.yaml` file as an input which has the format:

    ```
      gs_output_dir: xxxx
      release: 104
      resources:
        - 'caenorhabditis_elegans'
        ... many more species
        - 'canis_lupus_familiaris'
    ```
    Each resource needs two files downloaded:
        Compara.104.ncrna_default.homologies.tsv.gz        13-Mar-2021 21:08           126747131
        Compara.104.protein_default.homologies.tsv.gz      13-Mar-2021 18:48           119129028

    These are saved as  `<release>-<species>-[protein|rna].tsv.gz

    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.step_name = "Homologues"

    @staticmethod
    def download_protein_mapping_for_species(uri, staging, download, species: str) -> ManifestResource:
        """
        Download protein homology for species and suffix if file does not already exist.

        Most entries do not require suffix to be provided, but some such as sus_scrofa_usmarc have no standard ftp
        entries requiring a custom suffix.
        """
        # Create the resource info.
        download_resource = Dict()
        download_resource.uri = f"{uri}{species}/{species}.json"
        download_resource.output_filename = f'{species}.json'
        download_resource.output_dir = staging
        return download.ftp_download(download_resource)

    @staticmethod
    def download_homologies_for_species(uri_homologues: str, release, output, type: str, species: str,
                                        download) -> ManifestResource:
        """
        Download homology data for the given species and type.

        :param uri_homologues: base URI to the homology data
        :param release: Ensembl release number
        :param output: output directory information
        :param type: type of homology data to download
        :param species: species to download homology data for
        :param download: download service
        """
        # Create the resource info.
        download_resource = Dict()
        download_resource.uri = f"{uri_homologues}/{species}/Compara.{release}.{type}_default.homologies.tsv.gz"
        download_resource.output_filename = f'{type}-{species}.tsv.gz'
        download_resource.output_dir = output
        return download.ftp_download(download_resource)

    def extract_fields_from_json(self, input_file, conf, output, jq_cmd) -> str:
        """
        Extract the data defined by the JQ filter from the given input file

        :param input_file: source file to extract data from
        :param conf: configuration object
        :param output: information on where the output result should be place
        :param jq_cmd: JQ command for extracting data from the input file
        :return: destination file path of the extracted data content
        """
        head, tail = os.path.split(input_file)
        output_file = os.path.join(output.prod_dir, conf.path, str(
            conf.release), tail.replace('json', 'tsv'))
        self._logger.info(f"Extracting id and name from: '{input_file}' to '{output_file}'")
        with open(output_file, "ba+") as tsv:
            try:
                jqp = subprocess.Popen(f"{jq_cmd} '{conf.jq}' {input_file}",
                                       stdout=subprocess.PIPE,
                                       shell=True)
                tsv.write(jqp.stdout.read())
            except OSError as e:
                if e.errno == errno.ENOENT:
                    # handle file not found error.
                    self._logger.error(e)
                raise
        return output_file

    def download_protein_mapping_data(self, conf, output, cmd_conf, download) -> List[ManifestResource]:
        """
        Download the protein mapping data for the species of interest, as defined in the configuration file.

        :param conf: configuration object
        :param output: information on where the output result should be place
        :param cmd_conf: configuration for the command line
        :param download: download service
        """
        create_folder(os.path.join(output.prod_dir, conf.path,
                                   str(conf.path_protein_mapping)))
        jq_cmd = Utils.check_path_command("jq", cmd_conf.jq)
        ensembl_base_uri = conf.uri.replace("{release}", str(conf.release))
        mapping_data_manifests = []
        for species in conf.resources:
            # Download the protein files for each species of interest
            self._logger.debug(f'Downloading protein mapping files for {species}')
            download_manifest = self.download_protein_mapping_for_species(ensembl_base_uri, output.staging_dir,
                                                                          download,
                                                                          species)
            if download_manifest.status_completion == ManifestStatus.COMPLETED:
                download_manifest.status_completion = ManifestStatus.FAILED
                try:
                    download_manifest.path_destination = \
                        self.extract_fields_from_json(
                            download_manifest.path_destination, conf, output, jq_cmd)
                except Exception as e:
                    download_manifest.msg_completion = f"COULD NOT extract fields from Protein dataset at " \
                                                       f"'{download_manifest.path_destination}'" \
                                                       f" using JQ command '{jq_cmd}', due to error: {str(e)}"
                    self._logger.error(download_manifest.msg_completion)
                else:
                    self._logger.debug(
                        f"Protein mapping data for '{species}' download manifest destination path"
                        f" set to '{download_manifest.path_destination}',"
                        f" as final recipient for the sub-dataset"
                    )
                    download_manifest.msg_completion = \
                        f"Homologue '{species}' data, JQ filtered with '{conf.jq}'"
                    download_manifest.status_completion = ManifestStatus.COMPLETED
            mapping_data_manifests.append(download_manifest)
        return mapping_data_manifests

    def download_homology_data(self, conf, output, download) -> List[ManifestResource]:
        """
        Download the homology data for the species of interest.

        Files look like:
            Compara.<release>.[type]_default.homologies.tsv.gz -> <type>-<species>.tsv.gz
        where <species> is the species of interest and <type> is one of the specified in conf.types_homologues
        :param conf: configuration object
        :param output: information on where the output result should be place
        :param download: download object
        """
        output_folder = os.path.join(output.prod_dir,
                                     conf.path, str(conf.path_homologues))
        create_folder(output_folder)
        ensembl_base_uri = conf.uri_homologues.replace("{release}", str(conf.release))
        homology_data_manifests = []
        # Iterate over the species of interest to download the homology data, which is a pair of files like
        for species in conf.resources:
            self._logger.debug(f'Downloading homology files for {species}')
            for type in conf.types_homologues:
                homology_data_manifests.append(
                    self.download_homologies_for_species(
                        ensembl_base_uri, conf.release, output_folder, type, species, download)
                )
        return homology_data_manifests

    def process(self, conf, output, cmd_conf):
        """
        Homologues pipeline step implementation

        :param conf: step configuration object
        :param output: output information object for results from this step
        :param cmd_conf: command line configuration object for external tools
        """
        self._logger.info("[STEP] BEGIN, Homologues")
        download = DownloadResource(output.staging_dir)
        # TODO - Should I halt the step as soon as I face the first problem?
        manifest_step = get_manifest_service().get_step(self.step_name)
        # Download protein mapping data
        manifest_step.resources.extend(
            self.download_protein_mapping_data(conf, output, cmd_conf, download))
        # Download homology data
        manifest_step.resources.extend(
            self.download_homology_data(conf, output, download))
        get_manifest_service().compute_checksums(manifest_step.resources)
        if not get_manifest_service().are_all_resources_complete(manifest_step.resources):
            manifest_step.status_completion = ManifestStatus.FAILED
            manifest_step.msg_completion = "COULD NOT retrieve all the resources"
        # TODO - Validation
        if manifest_step.status_completion != ManifestStatus.FAILED:
            manifest_step.status_completion = ManifestStatus.COMPLETED
            manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, Homologues")

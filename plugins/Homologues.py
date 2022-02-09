from yapsy.IPlugin import IPlugin
import logging
import os
import errno
import subprocess
from addict import Dict
from modules.common.DownloadResource import DownloadResource
from modules.common.Utils import Utils
from modules.common import create_folder

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

    @staticmethod
    def download_species(uri, release, staging, download, species: str):
        """
        Download protein homology for species and suffix if file does not already exist.

        Most entries do not require suffix to be provided, but some such as sus_scrofa_usmarc have no standard ftp
        entries requiring a custom suffix.
        """
        protein_uri = f"{uri}{species}/{species}.json"
        # Create the resource info.
        resource_stage = Dict()
        resource_stage.uri = protein_uri
        resource_stage.output_filename = f'{release}-{species}.json'
        resource_stage.output_dir = staging
        return download.ftp_download(resource_stage)

    @staticmethod
    def extract_fields_from_json(input_file, conf, output, jq_cmd) -> str:
        """
        Extract the data defined by the JQ filter from the given input file

        :param input_file: source file to extract data from
        :param conf: configuration object
        :param output: information on where the output result should be place
        :param jq_cmd: JQ command for extracting data from the input file
        :return: destination file path of the extracted data content
        """
        head, tail = os.path.split(input_file)
        output_file = os.path.join(output.prod_dir, conf.path, str(conf.release), tail.replace('json', 'tsv'))
        logger.info(f"Extracting id and name from: {input_file}")
        with open(output_file, "ba+") as tsv:
            try:
                jqp = subprocess.Popen(f"{jq_cmd} '{conf.jq}' {input_file}",
                                       stdout=subprocess.PIPE,
                                       shell=True)
                tsv.write(jqp.stdout.read())
            except OSError as e:
                if e.errno == errno.ENOENT:
                    # handle file not found error.
                    logger.error(e)
                else:
                    # Something else went wrong
                    raise
        return output_file

    def process(self, conf, output, cmd_conf):
        download = DownloadResource(output.staging_dir)
        uri_release = conf.uri.replace("{release}", str(conf.release))
        create_folder(os.path.join(output.prod_dir, conf.path, str(conf.release)))
        jq_cmd = Utils.check_path_command("jq", cmd_conf.jq)
        for species in conf.resources:
            logger.debug(f'Downloading files for {species}')
            filename_json = self.download_species(uri_release, conf.release, output.staging_dir, download, species)
            self.extract_fields_from_json(filename_json, conf, output, jq_cmd)

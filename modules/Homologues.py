import os
import errno
from typing import Dict

import subprocess

from definitions import PIS_OUTPUT_HOMOLOGY
from .DownloadResource import DownloadResource

import logging

logger = logging.getLogger(__name__)


class Homologues(object):
    """
    Class to download resources from Ensembl FTP for use in ETL target step (specifically to generate homologues).

    Takes the `homology` section of the `config.yaml` file as an input which has the format:

    ```
      gs_output_dir: annotation-files/homology
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

    def __init__(self, yaml_dict, jq_cmd):
        self.config: Dict = yaml_dict
        self.gs_output_dir = yaml_dict.gs_output_dir
        self.list_files_downloaded = {}
        self.download = DownloadResource(PIS_OUTPUT_HOMOLOGY)
        self.jq = jq_cmd

        self.release = self.config.release
        self.uri = 'ftp://ftp.ensembl.org/pub/release-{release}/json/'.format(release=self.release)
        self.jq_output = f"{PIS_OUTPUT_HOMOLOGY}_{self.release}_id_name.tsv"

    def _download_if_not_present(self, resource: Dict):
        """
        Download requested file if it does not already exist.
        """
        path = os.path.join(self.download.output_dir, resource['output_filename'])
        if not os.path.isfile(path):
            return self.download.ftp_download(resource)
        else:
            logger.info(f"{resource['output_filename']} already downloaded, will not download again.")
            return path

    def download_species(self, species: str):
        """
        Download protein homology for species and suffix if file does not already exist.

        Most entries do not require suffix to be provided, but some such as sus_scrofa_usmarc have no standard ftp
        entries requiring a custom suffix.
        """
        protein_uri = self.uri + f"{species}/{species}.json"
        resource = {
            'uri': protein_uri,
            'output_filename': f'{self.release}-{species}.json',
            'output_dir': 'homologue',
            'resource': f'ensembl-homologue-{species}'
        }
        return self._download_if_not_present(resource)

    def extract_fields_from_json(self, input_file: str) -> str:

        output_file: str = input_file.replace('json', 'tsv')
        if not os.path.isfile(output_file):
            logger.info(f"Extracting id and name from: {input_file}")
            with open(output_file, "ba+") as tsv:
                try:
                    jqp = subprocess.Popen(f"{self.jq} '{self.config['jq']}' {input_file}",
                                                             stdout=subprocess.PIPE,
                                                             shell=True)
                    tsv.write(jqp.stdout.read())
                    return output_file

                except OSError as e:
                    if e.errno == errno.ENOENT:
                        # handle file not found error.
                        logger.error(e)
                    else:
                        # Something else went wrong
                        raise
        else:
            logger.info(f"{output_file} already processed into tsv, will not process again.")
            return output_file

    def download_resources(self):

        for species in self.config.resources:
            logger.debug(f'Downloading files for {species}')

            filename_json = self.download_species(species)

            filename_tsv = self.extract_fields_from_json(filename_json)

            self.list_files_downloaded[f'{species}-json'] = {
                'resource': filename_json,
                'gs_output_dir': self.gs_output_dir
            }
            self.list_files_downloaded[f'{species}-tsv'] = {
                'resource': filename_tsv,
                'gs_output_dir': self.gs_output_dir
            }

        return self.list_files_downloaded

import os
from typing import Dict

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

    def __init__(self, yaml_dict):
        self.config: Dict = yaml_dict
        self.gs_output_dir = yaml_dict.gs_output_dir
        self.list_files_downloaded = {}
        self.download = DownloadResource(PIS_OUTPUT_HOMOLOGY)

        self.release = self.config.release
        self.uri = 'ftp://ftp.ensembl.org/pub/release-{release}/tsv/ensembl-compara/homologies/'.format(release=
                                                                                                        self.release)

    def _download_if_not_present(self, resource: Dict):
        """
        Download requested file if it does not already exist.
        """
        if not os.path.isfile(os.path.join(self.download.output_dir, resource['output_filename'])):
            return self.download.ftp_download(resource)
        else:
            logger.info(f"{resource['output_filename']} already downloaded, will not download again.")

    def get_protein(self, species: str, ensembl_suffix="default"):
        """
        Download protein homology for species and suffix if file does not already exist.

        Most entries do not require suffix to be provided, but some such as sus_scrofa_usmarc have no standard ftp
        entries requiring a custom suffix.
        """
        protein_uri = self.uri + "{species}/Compara.{release}.protein_{suffix}.homologies.tsv.gz".format(
            species=species,
            release=self.release,
            suffix=ensembl_suffix)
        resource = {
            'uri': protein_uri,
            'output_filename': f'{self.release}-{species}-protein.tsv.gz',
            'output_dir': 'homologue',
            'resource': f'ensembl-homologue-{species}'
        }
        return self._download_if_not_present(resource)

    def get_rna(self, species: str, ensembl_suffix="default"):
        """
        Download rna homology for species and suffix if file does not already exist.

        Most entries do not require suffix to be provided, but some such as sus_scrofa_usmarc have no standard ftp
        entries requiring a custom suffix.
        """
        protein_uri = self.uri + "{species}/Compara.{release}.ncrna_{suffix}.homologies.tsv.gz".format(species=species,
                                                                                                       release=self.release,
                                                                                                       suffix=ensembl_suffix)
        resource = {
            'uri': protein_uri,
            'output_filename': f'{self.release}-{species}-rna.tsv.gz',
            'output_dir': 'homologue',
            'resource': f'ensembl-homologue-{species}'
        }
        return self._download_if_not_present(resource)

    def download_resources(self):
        custom_suffix_species = {
            'sus_scrofa_usmarc': "pig_breeds"
        }
        for species in self.config.resources:
            logger.debug(f'Downloading files for {species}')
            if species not in custom_suffix_species:
                protein = self.get_protein(species)
                rna = self.get_rna(species)
            else:
                protein = self.get_protein(species, custom_suffix_species[species])
                rna = self.get_rna(species, custom_suffix_species[species])

            self.list_files_downloaded[f'{species}-protein'] = {
                'resource': protein,
                'gs_output_dir': self.gs_output_dir
            }
            self.list_files_downloaded[f'{species}-rna'] = {
                'resource': rna,
                'gs_output_dir': self.gs_output_dir
            }

        return self.list_files_downloaded

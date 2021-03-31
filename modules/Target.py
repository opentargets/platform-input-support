import logging
import os
from ftplib import FTP
from typing import Dict, List
from definitions import PIS_OUTPUT_TARGET
from modules.DownloadResource import DownloadResource
from modules.common import extract_file_from_zip, make_ungzip

logger = logging.getLogger(__name__)


class Target(object):
    """
    Retrieve resources required for ETL Target step from Ensembl FTP.
    """

    def __init__(self, yaml):
        self.config = yaml
        self.ensembl_config = yaml.ensembl
        self.output_dir = PIS_OUTPUT_TARGET

        # ensembl ftp settings
        self.ensembl_ftp_url = self.ensembl_config.ensembl_ftp_url
        self.path = self.ensembl_config.path.replace('{suffix}', str(self.ensembl_config.release))

    def download_ftp(self, ftp_url: str, ftp_path: str, file: str, out_file_name: str) -> str:
        """
        download remote file to output_file_name. output_file_name is absolute path and name.
        """
        if os.path.isfile(out_file_name):
            logger.info(f"Found {out_file_name}: will not download again.")
            pass
        else:
            ftp = FTP(ftp_url)
            ftp.login()
            ftp.cwd(ftp_path)
            with open(out_file_name, 'wb') as outfile:
                logger.debug(f"Downloading {file} from {ftp_path} as {outfile.name}")
                ftp.retrbinary('RETR ' + file, outfile.write)
                return out_file_name

    def download_hpa(self) -> str:
        logger.info("Downloading HPA target files")
        download = DownloadResource(self.output_dir + "/hpa")
        downloaded_file = download.execute_download(self.config.hpa)
        return downloaded_file

    def download_project_scores(self) -> List[str]:
        logger.info("Downloading project scores target files")
        output_dir = os.path.join(self.output_dir, 'projectScores')
        # we only want one file from a zipped archive
        file_of_interest = 'EssentialityMatrices/04_binaryDepScores.tsv'
        _, fname = os.path.split(file_of_interest)
        download = DownloadResource(output_dir)
        downloaded_files = []
        for i in self.config.project_scores:
            if not os.path.exists(os.path.join(output_dir, fname)):
                f = download.execute_download(i)
                if f.endswith('.zip'):
                    downloaded_files.append(extract_file_from_zip(file_of_interest, f, output_dir))
                    if os.path.exists(f):
                        os.remove(f)
                else:
                    downloaded_files.append(f)
            else:
                logger.debug(f"Found {fname} in {output_dir}: will not download again.")
        return downloaded_files

    def download_go(self) -> List[str]:
        logger.info("Downloading gene ontology files.")
        ftp_url = self.config.go.url
        ftp_path_human = self.config.go.goa_human.path
        ftp_path_ensembl = self.config.go.goa_ensembl.path
        go_output_dir = self.output_dir + "/go/"

        # download human files
        files_to_download: List[str] = self.config.go.goa_human.files
        downloaded = []
        for f in files_to_download:
            output_location = go_output_dir + f
            downloaded.append(self.download_ftp(ftp_url, ftp_path_human, f, output_location))

        # download ensembl file
        downloaded.append(self.download_ftp(ftp_url,
                                            ftp_path_ensembl,
                                            self.config.go.goa_ensembl.filename,
                                            go_output_dir + self.config.go.goa_ensembl.filename))
        return downloaded

    def download_homo_sapiens(self) -> str:
        logger.info("Downloading ensembl homo_sapiens file.")
        ftp_path = self.path + self.ensembl_config.homo_sapiens.path
        file_to_download: str = self.ensembl_config.homo_sapiens.filename
        output_location: str = self.output_dir + "/ensembl/" + self.ensembl_config.homo_sapiens.filename
        return self.download_ftp(self.ensembl_ftp_url, ftp_path, file_to_download, output_location)

    def download_species(self) -> str:
        logger.info("Downloading target species file.")
        file_to_download = self.ensembl_config.species
        output_location = self.output_dir + "/ensembl/" + self.ensembl_config.species
        return self.download_ftp(self.ensembl_ftp_url, self.path, file_to_download, output_location)

    def download_ortholog(self) -> List[str]:
        logger.info("Downloading ortholog files.")
        ftp_path = self.path + self.ensembl_config.orthologs.path
        files_to_download: List[str] = self.ensembl_config.orthologs.files
        downloaded = []
        for f in files_to_download:
            fn = f.replace("{suffix}", str(self.ensembl_config.release))
            output_location = self.output_dir + "/ensembl/" + fn
            downloaded.append(self.download_ftp(self.ensembl_ftp_url, ftp_path, fn, output_location))
        return downloaded

    def download_gnomad(self):
        logger.info("Downloading gnomad files for target")
        download = DownloadResource(os.path.join(self.output_dir, "gnomad"))
        downloaded_file = download.execute_download(self.config.gnomad)
        unzipped = make_ungzip(downloaded_file)
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        return unzipped

    def download_ncbi(self):
        logger.info("Downloading ncbi files for target.")
        download = DownloadResource(os.path.join(self.output_dir, "ncbi"))
        downloaded_file = download.ftp_download(self.config.ncbi)
        return downloaded_file

    def create_output_dirs(self):
        directories = ["ensembl", "go", "hpa", "projectScores", "gnomad", "ncbi"]
        for d in directories:
            path = self.output_dir + "/" + d
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except OSError:
                    print("Creation of the directory %s failed" % d)
                else:
                    print("Successfully created the directory %s" % d)

    def execute(self) -> Dict[str, Dict[str, str]]:
        """
        Saves all files in `target` section of config to PIS_OUTPUT_TARGET
        """
        self.create_output_dirs()
        # Download files
        sources: List[str] = [self.download_species(),
                              self.download_homo_sapiens(),
                              self.download_hpa(),
                              self.download_gnomad(),
                              self.download_ncbi()]
        sources = sources + self.download_ortholog()
        sources = sources + self.download_go()
        sources = sources + self.download_project_scores()
        downloaded_files = {}
        for f in sources:
            downloaded_files[f] = {'resource': "{}".format(f), 'gs_output_dir': self.config[
                'gs_output_dir']}
        return downloaded_files



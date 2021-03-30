import logging
import os
from ftplib import FTP
from typing import Dict, List
from definitions import PIS_OUTPUT_TARGET

logger = logging.getLogger(__name__)


class TargetGo(object):
    def __init__(self):
        pass

    def execute(self):
        pass


class Target(object):
    """
    Retrieve resources required for ETL Target step from Ensembl FTP.
    """

    def __init__(self, yaml):
        self.config = yaml
        self.ensembl_config = yaml.ensembl
        self.output_dir = PIS_OUTPUT_TARGET

        # ensembl ftp settings
        self.url = self.ensembl_config.url
        self.path = self.ensembl_config.path.replace('{suffix}', str(self.ensembl_config.release))

    def download_ftp(self, ftp_path: str, file: str, out_file_name: str) -> str:
        """
        download remote file to output_file_name. output_file_name is absolute path and name.
        """
        if os.path.isfile(out_file_name):
            logger.info(f"Found {out_file_name}: will not download again.")
            pass
        else:
            ftp = FTP(self.url)
            ftp.login()
            ftp.cwd(ftp_path)
            with open(out_file_name, 'wb') as outfile:
                logger.debug(f"Downloading {file} from {ftp_path} as {outfile.name}")
                ftp.retrbinary('RETR ' + file, outfile.write)
                return out_file_name

    def download_homo_sapiens(self) -> str:
        logger.info("Downloading ensembl homo_sapiens file.")
        ftp_path = self.path + self.ensembl_config.homo_sapiens.path
        file_to_download: str = self.ensembl_config.homo_sapiens.filename
        output_location: str = self.output_dir + "/ensembl/" + self.ensembl_config.homo_sapiens.filename
        return self.download_ftp(ftp_path, file_to_download, output_location)

    def download_species(self) -> str:
        logger.info("Downloading target species file.")
        file_to_download = self.ensembl_config.species
        output_location = self.output_dir + "/ensembl/" + self.ensembl_config.species
        return self.download_ftp(self.path, file_to_download, output_location)

    def download_ortholog(self) -> List[str]:
        logger.info("Downloading ortholog files.")
        ftp_path = self.path + self.ensembl_config.orthologs.path
        files_to_download: List[str] = self.ensembl_config.orthologs.files
        downloaded = []
        for f in files_to_download:
            fn = f.replace("{suffix}", str(self.ensembl_config.release))
            output_location = self.output_dir + "/ensembl/" + fn
            downloaded.append(self.download_ftp(ftp_path, fn, output_location))
        return downloaded

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
                              self.download_homo_sapiens()]
        sources = sources + self.download_ortholog()
        downloaded_files = {}
        for f in sources:
            downloaded_files[f] = {'resource': "{}".format(f), 'gs_output_dir': self.config[
                'gs_output_dir']}
        return downloaded_files

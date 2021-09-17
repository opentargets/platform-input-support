import logging
import os
import subprocess
import shutil
from typing import Dict, List
from definitions import PIS_OUTPUT_TARGET
from modules.DownloadResource import DownloadResource
from modules.common import extract_file_from_zip, make_ungzip

logger = logging.getLogger(__name__)


def file_already_downloaded(file_to_download):
    """
    Returns whether a file already exists with the same name as the proposed download file.
    """
    return os.path.isfile(file_to_download)


class Target(object):
    """
    Retrieve resources required for ETL Target step from Ensembl FTP.
    """

    def __init__(self, yaml):
        self.config = yaml.target
        self.common = yaml.config
        self.output_dir = PIS_OUTPUT_TARGET

    def download_hpa(self) -> str:
        logger.info("Downloading HPA target files")
        path = os.path.join(self.output_dir, "hpa")
        download = DownloadResource(path)
        if not file_already_downloaded(os.path.join(path, self.config.hpa.output_filename)):
            return download.execute_download(self.config.hpa)

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


    def check_jq_path_command(self, cmd, yaml_cmd):
        """
        Check if the path for jq is available otherwise it uses the path provided in the config file.
        Return: jq path
        TODO: Duplication of the function in the Riot Module. Fix it.
        """
        cmd_result = shutil.which(cmd)
        if cmd_result == None:
            print(cmd+" not found. Using the path from config.yaml")
            cmd_result = yaml_cmd
        return cmd_result

    def download_and_process_ensembl(self, config: Dict, output_dir: str, jq_binary='/usr/bin/jq') -> str:
        """
        Downloads raw ensembl file, converts to jsonl and filters using jq filter before uploading.
        Return: downloaded file name.
        """
        jq_binary_x = self.check_jq_path_command(jq_binary,self.common.jq)

        jsonl_filename = os.path.join(output_dir, config.jq_filename)

        if file_already_downloaded(jsonl_filename):
            logger.debug("Ensembl jsonl exists, will not recompute.")
        else:
            logger.info("Converting Ensembl json file into jsonl.")
            raw_json = os.path.join(output_dir, config.output_filename)
            with open(jsonl_filename, "wb") as jsonwrite:
                jqp = subprocess.Popen([jq_binary_x, "-c", config.jq, raw_json], stdout=subprocess.PIPE)
                jsonwrite.write(jqp.stdout.read())

        return jsonl_filename

    def download_ftp_files(self, name: str, config: Dict, output_dir: str) -> List[str]:
        logger.info(f"Downloading {name} files.")
        download = DownloadResource(output_dir)
        downloaded_files = []
        for f in config:
            if not file_already_downloaded(os.path.join(output_dir, f.output_filename)):
                downloaded_files.append(download.ftp_download(f))
            else:
                logger.debug(f"{f.output_filename} already exists: will not download again.")

            if f.output_filename == "homo_sapiens.json":
                self.download_and_process_ensembl(f, output_dir)
        return downloaded_files

    def download_gnomad(self):
        logger.info("Downloading gnomad files for target")
        path = os.path.join(self.output_dir, "gnomad")
        download = DownloadResource(path)
        if not file_already_downloaded(os.path.join(path, "gnomad_lof_by_gene.csv")):
            downloaded_file = download.execute_download(self.config.gnomad)
            unzipped = make_ungzip(downloaded_file)
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
            return unzipped

    def download_ncbi(self):
        logger.info("Downloading ncbi files for target.")

        path = os.path.join(self.output_dir, "ncbi")
        download = DownloadResource(path)
        if not file_already_downloaded(os.path.join(path, self.config.ncbi.output_filename)):
            return download.ftp_download(self.config.ncbi)

    def download_reactome(self):
        logger.info("Downloading reactome files for target.")

        path = os.path.join(self.output_dir, "reactome")
        download = DownloadResource(path)
        if not file_already_downloaded(os.path.join(path, self.config.reactome.output_filename)):
            return download.execute_download(self.config.reactome)

    def create_output_dirs(self):
        directories = ["ensembl", "go", "hpa", "reactome","projectScores", "gnomad", "ncbi"]
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
        sources: List[str] = [self.download_hpa(),
                              self.download_gnomad(),
                              self.download_ncbi(),
                              self.download_reactome()]
        sources = sources + self.download_ftp_files("gene ontology", self.config.go,
                                                    os.path.join(self.output_dir, "go"))
        sources = sources + self.download_ftp_files("ensembl", self.config.ensembl, os.path.join(self.output_dir,
                                                                                                 "ensembl"))
        sources = sources + self.download_project_scores()
        downloaded_files = {}
        for f in sources:
            downloaded_files[f] = {'resource': "{}".format(f), 'gs_output_dir': self.config[
                'gs_output_dir']}
        return downloaded_files

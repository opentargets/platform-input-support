import logging
from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads
from modules.common import extract_file_from_zip, create_folder, make_gunzip, make_gzip, make_unzip_single_file
import subprocess
from addict import Dict
from modules.common.Utils import Utils
import os
logger = logging.getLogger(__name__)

"""

"""
class Target(IPlugin):
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def get_gnomad(self, gnomad, output):
        filename = Downloads.download_staging_http(output.staging_dir, gnomad)
        filename_unzip=make_gunzip(filename)
        gzip_filename=os.path.join(create_folder(os.path.join(output.prod_dir, gnomad.path)), gnomad.output_filename)
        make_gzip(filename_unzip, gzip_filename)

    def get_subcellular_location(self, sub_location, output):
        filename = Downloads.download_staging_http(output.staging_dir, sub_location)
        filename_unzip=make_unzip_single_file(filename)
        gzip_filename=os.path.join(create_folder(os.path.join(output.prod_dir, sub_location.path)), sub_location.output_filename)
        make_gzip(filename_unzip, gzip_filename)

    def extract_ensembl(self, ensembl, output, cmd):
        logger.info("Converting Ensembl json file into jsonl.")
        jq_cmd = Utils.check_path_command("jq", cmd.jq)
        resource_stage = Dict()
        resource_stage.uri = ensembl.uri.replace('{release}', str(ensembl.release))
        file_input = Downloads.download_staging_ftp(output.staging_dir, resource_stage)
        output_dir = os.path.join(output.prod_dir,ensembl.path )
        output_file = os.path.join(create_folder(output_dir), ensembl.output_filename)
        with open(output_file, "wb") as jsonwrite:
            jqp = subprocess.Popen([jq_cmd, "-c", ensembl.jq, file_input], stdout=subprocess.PIPE)
            jsonwrite.write(jqp.stdout.read())

    def get_project_scores(self, project_score_entry, output):
        logger.info("Downloading project scores target files")
        # we only want one file from a zipped archive
        file_of_interest = 'EssentialityMatrices/04_binaryDepScores.tsv'
        file_input = Downloads.download_staging_http(output.staging_dir, project_score_entry)
        output_dir = os.path.join(output.prod_dir,project_score_entry.path )
        create_folder(output_dir)
        extract_file_from_zip(file_of_interest, file_input, output_dir)

    def process(self, conf, output, cmd_conf):
        self._logger.info("Target step")
        Downloads(output.prod_dir).exec(conf)

        self.get_project_scores(conf.etl.project_scores, output)
        self.extract_ensembl(conf.etl.ensembl, output, cmd_conf)
        self.get_subcellular_location(conf.etl.subcellular_location, output)
        self.get_gnomad(conf.etl.gnomad, output)
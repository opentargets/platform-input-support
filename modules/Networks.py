from definitions import PIS_OUTPUT_ANNOTATIONS
from DownloadResource import DownloadResource
from EnsemblResource import EnsemblResource
from SparkHelpers import SparkHelpers
from common import make_ungzip, get_output_spark_files
import logging
import os

logger = logging.getLogger(__name__)

class OTNetwork(object):

    def __init__(self, yaml_dict):
        self.intact_info = yaml_dict.intact_info
        self.rna_central = yaml_dict.rna_central
        self.uniprot_info = yaml_dict.uniprot_info
        self.gs_output_dir = yaml_dict.gs_output_dir
        self.list_files_downloaded = []
        self.spark = self.init_spark()
        self.download = DownloadResource(PIS_OUTPUT_ANNOTATIONS)

    def init_spark(self):
        spark = SparkHelpers()
        spark.spark_init()
        return spark

    def download_ensembl(self):
        output_filename = PIS_OUTPUT_ANNOTATIONS + '/ensembl_protein_mapping.json'
        ensemblInfo = EnsemblResource()
        ensemblInfo.run()
        ensemblInfo.get_proteinIds().to_json(output_filename, orient='records', lines=True)
        self.list_files_downloaded.append(output_filename)

    def get_rna_central(self):
        rna_central_df = self.spark.load_file(self.download.ftp_download(self.rna_central), "csv", "false", "\t")
        rna_filename = PIS_OUTPUT_ANNOTATIONS+'/otnetworks/rnacentral'
        rna_central_df.write.format('json').save(rna_filename)
        return get_output_spark_files(rna_filename, ".json")


    def get_intact_info_file(self):
        return self.download.ftp_download(self.intact_info)

    def get_uniprot_info_file(self):
        protein_info_filename = make_ungzip(self.download.execute_download(self.uniprot_info))
        protein_info_df = self.spark.load_file(protein_info_filename, "csv", "false", "\t")
        protein_info_filename = PIS_OUTPUT_ANNOTATIONS+'/otnetworks/human-mapping'
        protein_info_df.write.format('json').save(protein_info_filename)
        return get_output_spark_files(protein_info_filename, ".json")

from definitions import PIS_OUTPUT_INTERACTIONS
from .DownloadResource import DownloadResource
from .EnsemblResource import EnsemblResource
from .SparkHelpers import SparkHelpers
from .common import make_ungzip, get_output_spark_files
import logging
import os

logger = logging.getLogger(__name__)

class Interactions(object):

    def __init__(self, yaml_dict):
        self.yaml =  yaml_dict
        self.gs_output_dir = yaml_dict.gs_output_dir
        self.list_files_downloaded = {}
        self.spark = self.init_spark()
        self.download = DownloadResource(PIS_OUTPUT_INTERACTIONS)


    def init_spark(self):
        spark = SparkHelpers()
        spark.spark_init()
        return spark

    def get_rna_central(self):
        rna_central_df = self.spark.load_file(self.download.ftp_download(self.yaml.rna_central), "csv", "false", "\t")
        rna_filename = PIS_OUTPUT_INTERACTIONS + '/' + self.yaml.rna_central.output_dir
        rna_central_df.write.format('json').save(rna_filename)
        return get_output_spark_files(rna_filename, ".json")


    def get_intact_info_file(self):
        return self.download.ftp_download(self.yaml.intact_info)

    def get_uniprot_info_file(self):
        protein_info_filename = make_ungzip(self.download.execute_download(self.yaml.uniprot_info))
        protein_info_df = self.spark.load_file(protein_info_filename, "csv", "false", "\t")
        protein_info_filename = PIS_OUTPUT_INTERACTIONS+ '/' + self.yaml.uniprot_info.output_dir
        protein_info_df.write.format('json').save(protein_info_filename)
        return get_output_spark_files(protein_info_filename, ".json")


    def getIntactResources(self):
        intact_info_filename = self.get_intact_info_file()
        self.list_files_downloaded[intact_info_filename] = {'resource': self.yaml.intact_info.resource,
                                                            'gs_output_dir': self.gs_output_dir}
        list_files_rna=self.get_rna_central()
        for rna_file in list_files_rna:
            self.list_files_downloaded[rna_file] = {'resource': self.yaml.rna_central.resource,
                                                          'gs_output_dir': self.gs_output_dir + '/' + self.yaml.rna_central.output_dir}
        list_files_human=self.get_uniprot_info_file()
        for human_filename in list_files_human:
            self.list_files_downloaded[human_filename] = {'resource': self.yaml.uniprot_info.resource,
                                                          'gs_output_dir': self.gs_output_dir +'/' + self.yaml.uniprot_info.output_dir}

        return self.list_files_downloaded
from definitions import PIS_OUTPUT_HOMOLOGY
from DownloadResource import DownloadResource
from common import make_ungzip
from addict import Dict
import csv
import shelve
from opentargets_urlzsource import URLZSource
import datetime
import json
import dumbdbm
import logging


import psutil

import pyspark
import pyspark.sql
import pyspark.sql.functions
from pyspark import *
from pyspark.sql import *
from pyspark.sql.types import *
from pyspark.sql.functions import *

logger = logging.getLogger(__name__)


class Homology(object):

    def __init__(self, yaml_dict):
        self.ensembl_release = yaml_dict.ensembl_release
        self.protein_coding = Dict()
        self.protein_coding.uri = yaml_dict.uri_protein_coding.replace('{ensembl_release}', str(self.ensembl_release))
        self.protein_coding.output_filename = 'protein.homologies.' + str(self.ensembl_release) + '.tsv.gz'
        self.ncRNAs = Dict()
        self.ncRNAs.uri = yaml_dict.uri_ncRNAs.replace('{ensembl_release}', str(self.ensembl_release))
        self.ncRNAs.output_filename = 'ncRNA.homologies.' + str(self.ensembl_release) + '.tsv.gz'
        self.ensembl_species_yaml = Dict()
        self.ensembl_species_yaml.uri = yaml_dict.uri_ensembl_species.replace('{ensembl_release}',
                                                                              str(self.ensembl_release))
        self.ensembl_species_yaml.output_filename = 'species_EnsemblVertebrates.' + str(self.ensembl_release) + '.txt'
        self.whitelisted_species = yaml_dict.whitelisted_species
        self.uri_ftp = yaml_dict.uri_ftp.replace('{ensembl_release}', str(self.ensembl_release))
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.gs_output_dir = yaml_dict.gs_output_dir
        self.ensembl_species = {}
        self.ensembl_taxonomy = {}
        self.homologies = []
        self.pyspark_mem=(psutil.virtual_memory().available) >>30


    def insert_species(self, row):
        self.ensembl_species.update({row["species"]: row["taxonomy_id"]})

    def get_species(self):
        print("todo")
        #self.ensembl_species = self.session.read.format("csv").option("header", "true").option("sep", "\t").load(self.species_file).filter(col("taxonomy_id").isin(self.whitelisted_species))


    # def get_species_old(self):
    #     download = DownloadResource(PIS_OUTPUT_HOMOLOGY)
    #     self.ensembl_taxonomy = {}
    #     with URLZSource(self.species_file).open() as species:
    #         reader = csv.DictReader(species, delimiter='\t', quoting=csv.QUOTE_NONE)
    #         for i, row in enumerate(reader, start=1):
    #             if row["taxonomy_id"] in self.whitelisted_species:
    #                 self.insert_species(row)

    def spark_init(self):
        conf = pyspark.SparkConf().setAll([('spark.executor.memory', str(self.pyspark_mem)+'g'), ('spark.executor.cores', '3'), ('spark.cores.max', '3'),  ('spark.driver.memory', str(self.pyspark_mem)+'g')])
        #sc = pyspark.SparkContext(conf=conf)
        #sc.getConf().getAll()
        #self.session = SQLContext(sc)

    # def run_spark(self):
    #     inf = '/home/cinzia/gitRepositories/platform-input-support/output/annotation-files/homology/Compara.100.protein_default.homologies.tsv'
    #     df = self.session.read.format("csv").option("header", "true").option("sep", "\t").load(inf)
    #     lista = ['sus_scrofa_berkshire', 'sus_scrofa_usmarc', 'mus_musculus_aj', 'sus_scrofa_bamei', 'pan_troglodytes',
    #              'sus_scrofa_largewhite', 'homo_sapiens', 'mus_musculus_fvbnj', 'caenorhabditis_elegans',
    #              'sus_scrofa_landrace', 'canis_lupus_familiaris', 'macaca_mulatta', 'mus_musculus_129s1svimj',
    #              'mus_musculus', 'danio_rerio', 'sus_scrofa_hampshire', 'sus_scrofa_jinhua', 'mus_musculus_nodshiltj',
    #              'mus_musculus_lpj', 'cavia_porcellus', 'mus_musculus_cbaj', 'drosophila_melanogaster',
    #              'canis_lupus_familiarisgreatdane', 'oryctolagus_cuniculus', 'rattus_norvegicus', 'mus_musculus_balbcj',
    #              'sus_scrofa_pietrain', 'sus_scrofa', 'sus_scrofa_wuzhishan', 'mus_musculus_dba2j',
    #              'mus_musculus_c57bl6nj', 'sus_scrofa_meishan', 'mus_musculus_nzohlltj', 'sus_scrofa_tibetan',
    #              'canis_lupus_familiarisbasenji', 'xenopus_tropicalis', 'sus_scrofa_rongchang', 'mus_musculus_c3hhej',
    #              'mus_musculus_akrj']
    #
    #     df2 = df.filter(col("homology_species").isin(lista))
    #
    #     specs = '/home/cinzia/gitRepositories/platform-input-support/output/annotation-files/homology/species_tsv/*.json'
    #     speciesDF = session.read.format("csv").option("header", "false").option("sep", "\t").load(spec)
    #     sp = speciesDF.withColumnRenamed("_c0", "homology_gene_stable_id")
    #
    #     tot = df2.join(sp, df2.homology_gene_stable_id == sp.homology_gene_stable_id, "inner").drop(
    #         sp.homology_gene_stable_id)
    #
    #     finale = tot.withColumnRenamed("gene_stable_id","id").withColumnRenamed("homology_species",
    #                                                                              "speciesId").withColumnRenamed(
    #         "homology_gene_stable_id", "targetGeneId").withColumnRenamed(
    #         "_c1", "targetGeneSymbol").withColumnRenamed("homology_species", "speciesName").withColumnRenamed(
    #         "homology_type", "homologyType").withColumnRenamed("identity", "queryPercentageIdentity").withColumnRenamed(
    #         "homology_identity", "targetPercentageIdentity")
    #
    #     finale.select("id", "speciesId", "speciesName", "homologyType", "targetGeneId", "targetGeneSymbol",
    #                   "queryPercentageIdentity", "targetPercentageIdentity").write.json("homologies")

    def download_files(self):
        download = DownloadResource(PIS_OUTPUT_HOMOLOGY)
        #self.species_file = download.ftp_download(self.ensembl_species_yaml)
        #self.ncRNAs_file = download.ftp_download(self.ncRNAs)
        #self.protein_coding_file = download.ftp_download(self.protein_coding)

    def generateHomology(self):
        self.download_files()
        self.spark_init()
        self.get_species()

        return "done"

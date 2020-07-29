from definitions import PIS_OUTPUT_OTNETWORK, PIS_OUTPUT_OTNETWORK_TMP
from DownloadResource import DownloadResource
from EnsemblResource import EnsemblResource
from SparkHelpers import SparkHelpers
from pyspark.sql.functions import *
from common import make_ungzip
import logging

logger = logging.getLogger(__name__)

class OTNetwork(object):

    def __init__(self, yaml_dict):
        self.intact_info = yaml_dict.intact_info
        self.rna_central = yaml_dict.rna_central
        self.uniprot_info = yaml_dict.uniprot_info
        self.gs_output_dir = yaml_dict.gs_output_dir
        self.rna_central_filename = None
        self.intact_info_filename = None
        self.uniprot_info_filename = None

    def init_spark(self):
        spark = SparkHelpers()
        spark.spark_init()
        self.spark = spark

    def get_ensembl(self):
        ensemblInfo = EnsemblResource()
        ensemblInfo.run()
        return self.spark.session.createDataFrame(ensemblInfo.get_proteinIds()).withColumnRenamed("protein_id", "mapped_id")

    def download_files(self):
        download = DownloadResource(PIS_OUTPUT_OTNETWORK_TMP)
        self.rna_central_filename = download.ftp_download(self.rna_central)
        self.intact_info_filename = download.ftp_download(self.intact_info)
        protein_info_filename = download.execute_download(self.uniprot_info)
        self.protein_info_filename = make_ungzip(protein_info_filename)

    def load_rna_mapping_info(self):
        return self.spark.load_file(self.rna_central_filename, "csv", "false", "\t")\
            .withColumnRenamed("_c0","mapped_id").withColumnRenamed("_c5", "gene_id").select("gene_id", "mapped_id")

    def load_uniprot_mapping_info(self):
        return self.spark.load_file(self.protein_info_filename, "csv", "false", "\t")\
            .filter(col("_c1") == "Ensembl").withColumnRenamed("_c0","mapped_id").withColumnRenamed("_c2", "gene_id").select("gene_id", "mapped_id")

    # ETL for intact info.
    def etl_intact_info(self):
        intactInfoDF = self.spark.load_file(self.intact_info_filename,"json")\
            .withColumn("interactorAId", col("interactorA.id")) \
            .withColumn("interactorAIdSource", col("interactorA.id_source")) \
            .withColumn("interactorBId", col("interactorB.id")) \
            .withColumn("interactorBIdSource", col("interactorB.id_source")) \
            .withColumn("sourceDatabase", col("source_info.source_database")) \
            .withColumn("interactionScore", col("interaction.interaction_score")) \
            .withColumn("causalInteraction", col("interaction.causal_interaction")) \
            .withColumn("organismA", col("interactorA.organism")).withColumn("organismB", col("interactorB.organism")) \
            .withColumn("biologicalRoleA", col("interactorA.biological_role")).withColumn("biologicalRoleB", col("interactorB.biological_role")) \
            .withColumn("evidences", explode(col("interaction.evidence"))) \
            .select("interactorAId", "interactorAIdSource", "organismA","interactorBId", "interactorBIdSource",
                    "organismB", "sourceDatabase","interactionScore","causalInteraction","evidences","biologicalRoleA",
                    "biologicalRoleB")

        # Todo:
        # Remove _ or -
        # interactorBId can be null. So it is an identify. InteractorB = InteractionA
        # Check if Ids are already EnsemblId -> targetA and targetB


        # rnaCentral manipulation. Some ID as _9606 added to the id. Remove them..filter(col("targetA").isNotNull())
        mappingLeftDF = intactInfoDF\
            .join(self.ensembl_mapping, split(col("interactorAId"), "_").getItem(0) == self.ensembl_mapping.mapped_id,how='left')\
            .withColumnRenamed("gene_id", "targetA")

        mappingDF = mappingLeftDF\
            .join(self.ensembl_mapping.alias("mapping"), split(col("interactorBId"), "_").getItem(0) == col("mapping.mapped_id"),how='left')\
            .withColumnRenamed("gene_id", "targetB")\
            .select("targetA","targetB","interactorAId", "interactorAIdSource", "interactorBId", "interactorBIdSource",
                    "organismA", "organismB", "sourceDatabase","interactionScore","causalInteraction","evidences",
                    "biologicalRoleA","biologicalRoleB")


        return mappingDF


    # it generates a dataframe with gene_id, mapped_id
    def mapping_info(self):
        # Get Ensembl - Protein ID mapping
        ensembl_proteidIds = self.get_ensembl()
        # Get Ensembl - rnaCentral mapping
        ensembl_rnaCentralIds = self.load_rna_mapping_info()
        # Get Ensembl - Protein ID mapping
        ensembl_uniprot = self.load_uniprot_mapping_info()

        ensembl_uniprot_valid = ensembl_proteidIds.select("gene_id")\
            .join(ensembl_uniprot,ensembl_proteidIds.gene_id == ensembl_uniprot.gene_id, "left")\
            .filter(col("mapped_id").isNotNull()).drop(ensembl_uniprot.gene_id)

        ensembl_rnaCentralIds_valid = ensembl_proteidIds.select("gene_id")\
            .join(ensembl_rnaCentralIds,ensembl_proteidIds.gene_id == ensembl_rnaCentralIds.gene_id,"left")\
            .filter(col("mapped_id").isNotNull()).drop(ensembl_rnaCentralIds.gene_id)

        # Create an unique dataframe with gene_id and mapping.
        self.ensembl_mapping = ensembl_proteidIds.union(ensembl_rnaCentralIds_valid).union(ensembl_uniprot_valid)


    def etl_interaction(self):
        #Init spark session
        self.init_spark()
        # Download all the files from yaml config.
        self.download_files()
        # Mapping info between Ensembl gene and the other resources.
        self.mapping_info()

        self.intractInfoDF = self.etl_intact_info()

        self.intractInfoDF.write.json(PIS_OUTPUT_OTNETWORK)

        return PIS_OUTPUT_OTNETWORK
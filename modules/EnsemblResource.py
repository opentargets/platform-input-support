#from definitions import PIS_OUTPUT_ANNOTATIONS
import json
import datetime
import logging
import pandas as pd
from sqlalchemy import create_engine
import os
import argparse
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
PIS_OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')
PIS_OUTPUT_ANNOTATIONS = os.path.join(PIS_OUTPUT_DIR, 'annotation-files')

logger = logging.getLogger(__name__)


class EnsemblResource(object):

    def __init__(self):
        self.VALID_CHROMOSOMES = [str(chr) for chr in range(1, 23)]+['X', 'Y', 'MT']
        self.ENSEMBL_DEFAULT_DB = 'homo_sapiens_core_100_38'
        self.enable_platform_mode = False
        self.enable_compression = True
        self.pipeline_file_name = None
        self.ensemblGenes = None

    def make_output_filename(self):
        """create the path if it does not exist for the filename and
        return the full filename
        """
        dirname = os.path.dirname(PIS_OUTPUT_ANNOTATIONS)
        filename = self.ENSEMBL_DEFAULT_DB + '_genes.json' + ('.gz' if self.enable_compression else '')

        if not os.path.exists(dirname) and dirname:
            os.mkdir(dirname)

        return os.path.join(dirname, filename)

    def check_compress_enabled(self, filename):
        return 'gzip' if filename.endswith('.gz') else None


    def build_database_url(self, ensembl_database):
        """ Build the correct URL based on the database required
        GRCh37 databases are on port 3337, all other databases are on port 3306
        """
        port = 3337 if str(ensembl_database).endswith('37') else 3306
        return 'mysql+mysqldb://anonymous@ensembldb.ensembl.org:{}/{}' \
            .format(port, ensembl_database)

    def build_ensembl_genes(self, enable_platform_mode, ensembl_database):
        """Queries the MySQL public ensembl database and outputs a gene lookup object in JSON format.
        Optionally write an additional file suitable for loading Ensembl gene data into the Open Targets pipeline.
        """

        # connect to Ensembl MySQL public server; port used will depend on Ensembl assembly version
        database_url = self.build_database_url(ensembl_database)
        print('Connecting to {}'.format(database_url))

        core = create_engine(database_url, connect_args={'compress': True})

        # SQL to retrieve required fields
        # Note that the single % in the LIKE clause have to be escaped as %%
        # Note. In order to run a left join the query slightly changed.
        q = """
        SELECT
        et.exon_id,
        et.transcript_id,
        g.stable_id AS gene_id,
        x.display_label AS gene_name,
        IFNULL(g.description, "") AS description,
        g.biotype,
        g.source,
        g.version,
        a.logic_name,
        r.name AS chr,
        g.seq_region_start AS start,
        g.seq_region_end AS end,
        e.seq_region_start AS exon_start,
        e.seq_region_end AS exon_end,
        tta.seq_region_strand AS fwdstrand,
        g.seq_region_strand AS strand,
        tta.stable_id AS protein_id
        FROM exon_transcript et, exon e, gene g, (select t.transcript_id, t.seq_region_strand, ta.stable_id from transcript t left join translation ta on ta.transcript_id = t.transcript_id) as tta, seq_region r, xref x, coord_system cs, analysis a
        WHERE
        g.canonical_transcript_id = et.transcript_id AND
        g.seq_region_id = r.seq_region_id AND
        x.xref_id = g.display_xref_id AND
        r.coord_system_id = cs.coord_system_id AND
        cs.name = 'chromosome' AND cs.attrib LIKE '%%default_version%%' AND
        g.analysis_id = a.analysis_id AND
        et.transcript_id = tta.transcript_id AND
        e.exon_id = et.exon_id
        """

        start_time = datetime.datetime.now()
        df = pd.read_sql_query(q, core, index_col='exon_id')

        # Only keep valid chromosomes
        df = df.loc[df.chr.isin(self.VALID_CHROMOSOMES), :]

        if (enable_platform_mode):

            # Create a new data frame with only unique gene_ids, and remove columns we don't need in the output
            df_pipeline = df.drop_duplicates(subset='gene_id')  # only store one of each gene
            df_pipeline = df_pipeline.drop(columns=['exon_start', 'exon_end', 'fwdstrand', 'transcript_id'])

            # Rename certain columns to those required by the pipeline
            df_pipeline = df_pipeline.rename(index=str, columns={"gene_id": "id", "chr": "seq_region_name",
                                                                 "gene_name": "display_name"})

            # Add columns derived from the meta table
            df_pipeline['assembly_name'] = self.get_meta(core, 'assembly.default')
            df_pipeline['db_type'] = self.get_meta(core, 'schema_type')
            df_pipeline['ensembl_release'] = self.get_meta(core, 'schema_version')
            df_pipeline['species'] = self.get_meta(core, 'species.production_name')

            # Add static columns, required by the pipeline
            df_pipeline['object_type'] = 'Gene'
            # all on valid chromosomes so this will always be true
            df_pipeline['is_reference'] = True

            self.ensemblGenes = df_pipeline
        else:
            # Get TSS determined by strand
            df['fwdstrand'] = df['fwdstrand'].map({1: True, -1: False})
            df['tss'] = df.apply(lambda row: row['start']
            if row['fwdstrand'] else row['end'], axis=1)

            # Flatten exon list
            df['exons'] = list(zip(df.exon_start, df.exon_end))
            exons_df = df.groupby('gene_id')['exons'].apply(
                self.flatten_exons).reset_index()

            # Merge exons to genes
            keepcols = ['gene_id', 'gene_name', 'description', 'biotype', 'chr', 'tss', 'start', 'end', 'fwdstrand','protein_id']
            genes = pd.merge(df.loc[:, keepcols].drop_duplicates(), exons_df, on='gene_id', how='inner')

            # For clickhouse bools need to converted (0, 1)
            genes.fwdstrand = genes.fwdstrand.replace({False: 0, True: 1})

            # Print chromosome counts
            print(genes['chr'].value_counts())

            # Test
            print('Number of genes: {}'.format(genes.gene_id.unique().size))
            for gene in ['ENSG00000169972', 'ENSG00000217801', 'ENSG00000272141']:
                print('{} is in dataset: {}'.format(
                    gene, gene in genes.gene_id.values))

            # Save json
            genes = genes.sort_values(['chr', 'start', 'end'])
            genes = genes.fillna(value='')
            self.ensemblGenes = genes

        print("Genes table completed in {0}.".format(datetime.datetime.now() - start_time))

    def flatten_exons(self, srs):
        ''' Flattens pd.Series list of lists into a single list.
        Clickhouse requires the list to be represented as a string with no spaces.

        Args:
            srs (pd.Series): Series containing list of lists
        Returns:
            (str): string representation of flatttened list
        '''
        flattened_list = [item for sublist in srs.tolist() for item in sublist]
        assert (len(flattened_list) % 2 == 0)
        # return str(flattened_list).replace(' ', '')
        return json.dumps([int(x) for x in flattened_list], separators=(',', ':'))

    # Retrieve specific values from the Ensembl meta table
    def get_meta(self, connection, field):
        result = connection.execute("SELECT meta_value FROM meta WHERE meta_key='{}'".format(field))
        records = result.fetchall()
        return records[0][0]

    def save(self):
        if self.pipeline_file_name:
            self.filename = self.make_output_filename()
            self.ensemblGenes.to_json(self.pipeline_file_name, orient='records', lines=True,
                          compression=self.check_compress_enabled(self.pipeline_file_name))

    def run(self):
        logging.info("Download Ensembl Info. It might require a couple of minutes...")
        self.build_ensembl_genes(self.enable_platform_mode, self.ENSEMBL_DEFAULT_DB)
        return self.ensemblGenes

    def get_proteinIds(self):
        proteinFilterPD = self.ensemblGenes[['gene_id', 'protein_id']]
        proteinPD = proteinFilterPD.loc[proteinFilterPD['protein_id'] != '']
        return proteinPD
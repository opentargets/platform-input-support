from definitions import PIS_OUTPUT_INTERACTIONS
import logging
import json
import requests
import gzip
import pandas as pd
import re
from io import BytesIO
from .DownloadResource import DownloadResource
import python_jsonschema_objects as pjo
from .common import replace_suffix

logger = logging.getLogger(__name__)


class StringInteractions(object):
    """
    main interface of the StringInteractions module.
    * Manages the flow of accessing data from various sources + mapping
    * Manages the formatting of the resulting data accomodating the json schema
    """

    def __init__(self, yaml_dict):
        self.download = DownloadResource(PIS_OUTPUT_INTERACTIONS)
        self.gs_output_dir = yaml_dict.gs_output_dir
        self.output_folder = PIS_OUTPUT_INTERACTIONS
        self.string_url = yaml_dict.string_info.uri
        self.score_limit = yaml_dict.string_info.score_threshold
        self.ensembl_gtf_url = yaml_dict.string_info.additional_resouces.ensembl_ftp
        self.network_json_schema_url = yaml_dict.string_info.additional_resouces.network_json_schema.url
        self.output_string = yaml_dict.string_info.output_string
        self.output_protein_mapping = yaml_dict.string_info.additional_resouces.ensembl_ftp.output_protein_mapping
        self.list_files_downloaded = {}


    def getStringResources(self):
        # Fetch string network data and generate evidence json:
        ensembl_protein_mapping = self.get_ensembl_protein_mapping()
        self.list_files_downloaded[ensembl_protein_mapping] = {'resource': None,
                                                      'gs_output_dir': self.gs_output_dir }
        string_file = self.fetch_data()
        self.list_files_downloaded[string_file] = {'resource': None,
                                                  'gs_output_dir': self.gs_output_dir }

        return self.list_files_downloaded



    def fetch_ensembl_mapping(self, ensembl_gtf_url):
        """
        Fetch gtf file from ensembl.
        """

        output_file = self.output_folder+'/'+ replace_suffix(self.output_protein_mapping)

        # Open gtf as dataframe:
        target_id_mapping_df = pd.read_csv(ensembl_gtf_url, sep='\t', skiprows=5, header=0,
                                           usecols=[2, 8], names=['type', 'annotation'])


        # Filtering data for CDS:
        target_id_mapping_df = target_id_mapping_df.loc[target_id_mapping_df.type == 'CDS']
        gene_id_pattern = re.compile(r'ENSG\d+')
        prot_id_pattern = re.compile(r'ENSP\d+')
        gene_map_list = target_id_mapping_df.annotation.apply(lambda row: {'gene_id': gene_id_pattern.findall(row)[0],
                                                                           'protein_id': prot_id_pattern.findall(row)[
                                                                               0]}).to_list()
        with gzip.open(output_file, 'wt') as f:
            json.dump(gene_map_list, f)

        return output_file

    def get_ensembl_protein_mapping(self):
        ensembl_file = self.download.ftp_download(self.ensembl_gtf_url)
        return self.fetch_ensembl_mapping(ensembl_file)

    def fetch_data(self):

        # Initialize fetch object:
        string = PrepareStringData(self.string_url, score_limit=self.score_limit)

        # Fetch network data:
        string.fetch_network_data()

        # Adding species information:
        string.map_organism()

        self.network_data = string.get_data()

        stringEntries = self.generate_json()

        output_file = self.output_folder+'/'+replace_suffix(self.output_string)

        logging.info('Saving table to: .... ' + output_file)

        # Save gzipped json file:
        with gzip.open(output_file, "wt") as f:
            stringEntries.apply(lambda x: f.write(str(x)+'\n'))

        return output_file


    def generate_json(self):

        sjg = StringJsonGenerator(self.network_json_schema_url)

        # Generate json objects:
        json_objects = self.network_data.apply(sjg.generate_network_object, axis=1)

        return json_objects


class PrepareStringData(object):
    """
    This class fetches STRING data enriches with organism data + maps ensembl protein id to gene id
    """
    
    # So far we are only getting ready to handle Homo sapiens:
    organisms = {
        '9606': {
            "taxId": "9606",
            "scientificName": "Homo sapiens",
            "commonName": "human",
        }
    }
    
    def __init__(self, string_url, version = None, score_limit = None):
        
        # save network URL:
        self.__string_url = string_url
        
        # Parse data version if not provided:
        if version:
            self.__version = version
        else:
            self.__version = self.parse_version( )
            
        # Provide some feedback to the log:
        self.score_limit = score_limit
            
        print('String network data initialized.')
     
    
    @staticmethod
    def __fetch_data__(string_url, usecol=None, separator=" ", names = None):
        """
        This function fetches the string datafile and does a first round of formatting. 
        Sending user agent in request header is required to fetch the data.

        input: URL
        output: pandas dataframe
        """

        # Programmatic access to the data is not allowed, we need to do this trick:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0"}

        # Submit requeset:
        try:
            response = requests.get(string_url, headers=headers)
        except Exception as e:
            e.args = ['[Error] the provided URL ({}) could not be processed.'.format(string_url)]
            raise e
            
        # Test output code:
        if response.status_code != 200:
            raise ValueError('')

        # Content piped through byte stream converter:
        try:
            if usecol:
                string_df = pd.read_csv(BytesIO(response.content), compression='gzip',sep=separator, usecols=usecol, names=names)
            else:
                string_df = pd.read_csv(BytesIO(response.content), compression='gzip',sep=separator)
        except Exception as e:
            raise e

        return (string_df)
    
    
    def parse_version(self):
        """
        Based on the stored string URL, this method parses the version of the data
        """
        
        version_regexp = 'v\d+\.\d+' # matching v11.0
        parsed_version = None

        m = re.search(version_regexp, self.__string_url)
        if m:
            parsed_version = m.group(0)
    
        print(('Parsed version: {}'.format(parsed_version)))
        return parsed_version
    
    
    def fetch_network_data(self, filename = None):
        
        if filename:
            self.__network_data__ = pd.read_csv(filename, sep = '\t')
            print('[Info] String data with network_data association is loaded')
            return
        
        # Fetch data:
        string_data = self.__fetch_data__(self.__string_url)
        print('[Info] String data with string_data association is downloaded')
        
        # Filter data for the score threshold:
        if self.score_limit:
            string_data = string_data.loc[string_data.combined_score >= self.score_limit]
            string_data.reset_index(inplace=True)
            print('[Info] String table filtered for interactions with score >= score_limit.')
            print('[Info] Number of remaining interactions string_data.')
            
        print(string_data)
        # Split organism for proteinA:
        new = string_data.protein1.str.split('.', expand=True)
        string_data['organism_A'] = new[0]
        string_data['interactor_A'] = new[1]

        # Split organism for proteinB:
        new = string_data.protein2.str.split('.', expand=True)
        string_data['organism_B'] = new[0]
        string_data['interactor_B'] = new[1]
        
        # Drop original column:
        string_data.drop(columns =["protein1", "protein2"], inplace = True)
        
        # Adding version:
        string_data['version'] = self.__version
        
        # Print out some report:
        self.__network_data__ = string_data


    def map_organism(self):
        
        species = self.organisms
        df = self.__network_data__
        
        # Setting type:
        df.organism_A = df.organism_A.astype(str)
        df.organism_B = df.organism_B.astype(str)
        
        # Looking up all organisms to for interactor A:
        organism_a = df.organism_A.apply(lambda x:  {'scientific_name_A': species[x]['scientificName'],  'common_name_A':  species[x]['commonName']} if x in species else {'scientific_name_A': None,  'common_name_A':  None})
        organism_a_df = pd.DataFrame(organism_a.tolist())
        print((organism_a_df.head()))
        
        # Adding to table:
        df = df.merge(organism_a_df, left_index=True, right_index=True)

        # Looking up all organisms for interactor B:
        organism_b = df.organism_B.apply(lambda x: {'scientific_name_B': species[x]['scientificName'],  'common_name_B':  species[x]['commonName']} if x in species else {'scientific_name_B': None,  'common_name_B':  None})
        organism_b_df = pd.DataFrame(organism_b.tolist())
        print((organism_b_df.head()))
        
        # Adding to table:
        df = df.merge(organism_b_df, left_index=True, right_index=True)
        
        # Update data:
        self.__network_data__ = df.astype(str)

        
    def save_table(self, output_filename='test.tsv'):
        # Save file as tsv:
        if output_filename.endswith('.tsv'):
            self.__network_data__.to_csv(output_filename, sep = '\t', index=False)
        elif output_filename.endswith('.json'):
            self.__network_data__.to_json(output_filename, orient="records")
        else:
            raise ValueError('File format: {output_filename.split(".")[-1]} could not be parsed.')
   
    def get_data(self):
        try:
            return self.__network_data__
        except:
            return None
   

    def __len__(self):
        
        try:
            return len(self.__network_data__)
        except Exception as e:
            return(None)


class StringJsonGenerator(object):
    
    # Source database name:
    sourceDb = 'string'
    
    # The following STRING channels can be mapped to detection methods on MI onotology:
    detection_method_mapping = {
        'coexpression': {'name': 'coexpression', 'mi_id': 'MI:2231'},
        'coexpression_transferred': {'name': 'coexpression_transferred', 'mi_id': ''},
        'neighborhood': {'name': 'neighborhood', 'mi_id': 'MI:0057'},
        'neighborhood_transferred': {'name': 'neighborhood_transferred', 'mi_id': ''},
        'fusion': {'name': 'fusion', 'mi_id': 'MI:0036'},
        'homology': {'name': 'homology', 'mi_id': 'MI:2163'},
        'experiments': {'name': 'experiments', 'mi_id': 'MI:0591'},
        'experiments_transferred': {'name': 'experiments_transferred', 'mi_id': ''},
        'cooccurence': {'name': 'cooccurence', 'mi_id': 'MI:2231'},
        'database': {'name': 'database', 'mi_id': ''},
        'database_transferred': {'name': 'database_transferred', 'mi_id': ''},
        'textmining': {'name': 'textmining', 'mi_id': 'MI:0110'},
        'textmining_transferred': {'name': 'textmining_transferred', 'mi_id': ''},
    }

    
    def __init__(self, schema_json_url):

        self.schema_json_url = schema_json_url
        self.schema_json = { "description": "Open Targets Network objects",
          "title": "Open Targets Network","type": "object","schema": "http://json-schema.org/draft-04/schema#"
        }
        self.builder = pjo.ObjectBuilder(self.schema_json)
        self.network_builder = self.builder.build_classes()

    def generate_network_object(self, row):
        
        # Save row:
        self.__row__ = row

        # Validate 1: excluding evidence with no ensembl gene id:
        if (row['interactor_A'] is None) or (row['interactor_B'] is None):
            return

        logging.info("Generating " + row['interactor_A'])

        # Generate target objects:
        interactorA =  self.generate_interactor(
            scientific_name=row['scientific_name_A'],
            tax_id=row['organism_A'], 
            common_name=row['common_name_A'],
            interactor_id=row['interactor_A'],
            source_db='ensembl_protein')

        interactorB = self.generate_interactor(
            scientific_name=row['scientific_name_B'],
            tax_id=row['organism_B'], 
            common_name=row['common_name_B'],
            interactor_id=row['interactor_B'],
            source_db='ensembl_protein')

        # Compiling properties into evidence:
        try:
            interaction = self.network_builder.OpenTargetsNetwork(
                interactorA = interactorA,
                interactorB = interactorB,
                interaction = self.generate_interaction(row),
                source_info = self.generate_source_info(self.sourceDb, '11'),
            )

            return interaction.serialize()
        except Exception as inst:
            print(type(inst))  # the exception instance
            logging.warning('Evidence generation failed for row: {}'.format(row.name))


        
    def generate_interactor(self, scientific_name, tax_id, common_name, interactor_id, source_db, biological_role="unspecified role"):
        """
        This function generates the interactor object.
        """
        return {
            'organism': {
                "scientific_name": scientific_name,
                "taxon_id": int(tax_id),
                "mnemonic": common_name
            },
            'biological_role': biological_role,
            'id': interactor_id,
            'id_source': source_db
        }

    def generate_source_info(self, source_name, version=None):
        """
        This function generates the source info object.
        """
        dict1 = {'source_database': source_name, 'database_version': version}
        return dict1

    def generate_evidence(self, method, score=None):
        """
        This function generates 
        """
        detection_method_short_name = self.detection_method_mapping[method]['name']
        detection_method_mi = self.detection_method_mapping[method]['mi_id']

        return {
            "interaction_identifier": None,
            "interaction_detection_method_short_name": detection_method_short_name,
            "interaction_detection_method_mi_identifier": detection_method_mi,
            "pubmed_id": None,
            "evidence_score": int(score)
        }

    def generate_interaction(self, row):
        # Initializing interaction:
        interaction = {
            "interaction_score": int(row['combined_score']),
            "causal_interaction": False,
        }

        # Generate list of evidence:
        evidences = []
        for method in list(self.detection_method_mapping.keys()):
            if method in row:
                evidences.append(self.generate_evidence(method,row[method]))

        # Add evidence to interaction:
        interaction['evidence'] = evidences

        return interaction

    def fetch_schema(self):

        # Submit requeset:
        try:
            response = requests.get(self.schema_json_url)
        except Exception as e:
            e.args = ['[Error] the provided URL ({}) could not be processed.'.format(self.schema_json_url)]
            raise e
            
        # Test output code:
        if response.status_code != 200:
            raise ValueError('')

        # Return the processed json:
        return response.json()



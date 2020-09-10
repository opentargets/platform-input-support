from definitions import PIS_OUTPUT_ANNOTATIONS
import logging
import os


logger = logging.getLogger(__name__)


class StringNetwork(object):
    """
    This class is used to fetch and process STRING datafile and formats it following the networks schema.
    """

    # Source database name:
    source_db = 'string'
    
    # The following STRING channels can be mapped to detection methods on MI onotology:
    detection_method_mapping = {
        'coexpression': {'name': 'coexpression', 'mi_id': 'MI:2231'},
        'coexpression_transferred' : {'name': 'coexpression_transferred', 'mi_id': ''},

        'neighborhood' : {'name': 'gene neighbourhood', 'mi_id': 'MI:0057'},
        'neighborhood_transferred' : {'name': 'neighborhood_transferred', 'mi_id': ''},

        'fusion' : {'name': 'domain fusion', 'mi_id': 'MI:0036'},

        'homology' : {'name': 'by homology', 'mi_id': 'MI:2163'},

        'experiments' : {'name': 'experiment description', 'mi_id': 'MI:0591'},
        'experiments_transferred': {'name':'experiments_transferred','mi_id':''},

        'cooccurence' : {'name': 'coexpression', 'mi_id': 'MI:2231'},

        'database' : {'name': 'database', 'mi_id': ''},
        'database_transferred': {'name':'database_transferred','mi_id':''},    

        'textmining' : {'name': 'text mining', 'mi_id': 'MI:0110'},
        'textmining_transferred': {'name':'textmining_transferred','mi_id':''},     
    }


    def __init__(self, yaml_dict):
        self.string_info = yaml_dict.string_info
        self.gs_output_dir = yaml_dict.gs_output_dir
        self.list_files_downloaded = []

        self.string_db_version = self.parsed_version()

    @staticmethod
    def __fetch_data__(url, usecol=None, separator=" ", names = None):
        """
        This function fetches the string datafile and does a first round of formatting. 
        Sending user agent in request header is required to fetch the data.

        input: URL
        output: pandas dataframe
        """

        # Programmatic access to the data is not allowed, we need to do this trick:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0"}

        # Submit request:
        try:
            response = requests.get(url, headers=headers)
        except Exception as e:
            e.args = ['[Error] the provided URL ({}) could not be processed.'.format(url)]
            raise e
            
        # Test output code:
        if response.status_code != 200:
            raise ValueError('[Error] the provided URL ({}) could not be processed.'.format(url))

        # Content piped through byte stream converter:
        try:
            if usecol:
                df = pd.read_csv(BytesIO(response.content), compression='gzip',sep=separator, usecols=usecol, names=names)
            else:
                df = pd.read_csv(BytesIO(response.content), compression='gzip',sep=separator)
        except Exception as e:
            raise e
            
        return df


    def format_string_data(self):
        return 1

    def save_data(self):
        return 1


    def parse_version(self):
        """
        Based on the stored string URL, this method parses the version of the data
        """
        
        version_regexp = 'v\d+\.\d+' # matching v11.0
        parsed_version = None

        m = re.search(version_regexp, self.self.string_info.url)
        if m:
            parsed_version = m.group(0)
    
        logger.info('String version: {}'.format(parsed_version))
        return parsed_versio


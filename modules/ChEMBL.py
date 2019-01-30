import os
import logging
from definitions import PIS_OUTPUT_CHEMBL_API
from time import sleep
from modules.common import URLZSource
import json
import datetime

def get_chembl_url(uri, filename, suffix):
    '''return to json from uri'''
    next_get = True
    limit = 1000000
    offset = 0
    uri_to_filename = PIS_OUTPUT_CHEMBL_API+'/'+filename.replace('{suffix}', suffix)
    if os.path.exists(uri_to_filename): os.remove(uri_to_filename)
    file_chembl = open(uri_to_filename, "a+")

    def _fmt(**kwargs):
        '''generate uri string params from kwargs dict'''
        l = ['='.join([k, str(v)]) for k, v in kwargs.iteritems()]
        return '?' + '&'.join(l)

    while next_get:
        sleep(0.1)  # Time in seconds. Slow down to avoid 429
        chunk = None
        with URLZSource(uri + _fmt(limit=limit, offset=offset)).open() as f:
            chunk = json.loads(f.read())

        page_meta = chunk['page_meta']
        data_key = list(set(chunk.keys()) - set(['page_meta']))[0]

        if 'next' in page_meta and page_meta['next'] is not None:
            limit = page_meta['limit']
            offset += limit
        else:
            next_get = False

        for el in chunk[data_key]:
            file_chembl.write(json.dumps(el))
            #yield el

    return uri_to_filename

class ChEMBLLookup(object):
    def __init__(self,yaml_dict):
        super(ChEMBLLookup, self).__init__()
        self._logger = logging.getLogger(__name__)

        self.target_cfg = yaml_dict.target
        self.mechanism_cfg = yaml_dict.mechanism
        self.component_cfg = yaml_dict.target_component
        self.protein_cfg = yaml_dict.protein_class
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')


    def download_targets(self):
        '''download the REST API associated to the uri'''
        self._logger.info('ChEMBL getting targets from ' + self.target_cfg.uri)
        targets_filename = get_chembl_url(self.target_cfg.uri, self.target_cfg.output_filename, self.suffix)

        return targets_filename

    def download_mechanisms(self):
        '''download the REST API associated to the uri'''
        self._logger.info('ChEMBL getting mechanism from ' + self.mechanism_cfg.uri)
        mechanisms_filename = get_chembl_url(self.mechanism_cfg.uri,self.mechanism_cfg.output_filename, self.suffix)

        return mechanisms_filename

    def download_protein_classification(self):
        '''download the REST API associated to the uri'''
        self._logger.info('ChEMBL getting protein classification from ' + self.component_cfg.uri)
        targets_components_filename = get_chembl_url(self.component_cfg.uri,
                                                     self.component_cfg.output_filename, self.suffix)

        return targets_components_filename

    def download_protein_class(self):
        '''download the REST API associated to the uri'''
        self._logger.info('ChEMBL getting protein from ' + self.protein_cfg.uri)
        protein_classes_filename = get_chembl_url(self.protein_cfg.uri,
                                                  self.protein_cfg.output_filename, self.suffix)

        return protein_classes_filename

    def download_chEMBL_files(self):
        list_files_ChEMBL_downloaded = []
        self._logger.info('chembl downloading targets/mechanisms/proteins')
        list_files_ChEMBL_downloaded.append(self.download_targets())
        list_files_ChEMBL_downloaded.append(self.download_mechanisms())
        list_files_ChEMBL_downloaded.append(self.download_protein_classification())
        list_files_ChEMBL_downloaded.append(self.download_protein_class())
        return list_files_ChEMBL_downloaded
import os
from definitions import PIS_OUTPUT_CHEMBL_API
from time import sleep
from opentargets_urlzsource import URLZSource
import json
import datetime
from common import make_gzip

import logging

logger = logging.getLogger(__name__)

def get_chembl_url(uri, filename, suffix):
    '''return to json from uri'''
    def _fmt(**kwargs):
        '''generate uri string params from kwargs dict'''
        l = ['='.join([k, str(v)]) for k, v in kwargs.iteritems()]
        return '?' + '&'.join(l)

    next_get = True
    limit = 1000000
    offset = 0
    uri_to_filename = PIS_OUTPUT_CHEMBL_API+'/'+filename.replace('{suffix}', suffix)
    if os.path.exists(uri_to_filename): os.remove(uri_to_filename)
    with open(uri_to_filename, "a+") as file_chembl:

        while next_get:
            sleep(0.1)  # Time in seconds. Slow down to avoid 429
            chunk = None
            logging.debug("uri:  %s %s %s", uri, limit, offset)

            with URLZSource(uri + _fmt(limit=limit, offset=offset)).open() as f:
                chunk = json.loads(f.read())

                page_meta = chunk.pop('page_meta', None)

                dict_key = chunk.keys()[0]

                for el in chunk[dict_key]:
                    file_chembl.write(json.dumps(el) + '\n')

            if 'next' in page_meta and page_meta['next'] is not None:
                limit = page_meta['limit']
                offset += limit

            else:
                next_get = False

    return uri_to_filename

class ChEMBLLookup(object):
    def __init__(self,yaml_dict):
        super(ChEMBLLookup, self).__init__()
        self._logger = logging.getLogger(__name__)

        self.target_cfg = yaml_dict.downloads.target
        self.mechanism_cfg = yaml_dict.downloads.mechanism
        self.component_cfg = yaml_dict.downloads.target_component
        self.protein_cfg = yaml_dict.downloads.protein_class
        self.molecule_cfg = yaml_dict.downloads.molecule
        self.drug_cfg = yaml_dict.downloads.drug
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.gs_output_dir = yaml_dict.gs_output_dir

    def download_targets(self):
        """download the REST API associated to the uri"""
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

    def download_molecules(self):
        '''download the REST API associated to the uri'''
        self._logger.info('ChEMBL getting molecules from ' + self.molecule_cfg.uri)
        molecules_filename = get_chembl_url(self.molecule_cfg.uri, self.molecule_cfg.output_filename, self.suffix)

        return molecules_filename


    def download_chEMBL_resources(self):
        """
        Downloads ChEMBL files and returns dictionary of filename -> {resource: ..., gs_output_dir: ...}
        """
        list_files_ChEMBL_downloaded = {}
        self._logger.info('chembl downloading drugs/molecules/targets/mechanisms/proteins')

        list_files_ChEMBL_downloaded[self.download_drugs()] = {'resource': self.drug_cfg.resource,
                                                                   'gs_output_dir': self.gs_output_dir }
        list_files_ChEMBL_downloaded[self.download_molecules()] = {'resource': self.molecule_cfg.resource,
                                                                   'gs_output_dir': self.gs_output_dir }
        list_files_ChEMBL_downloaded[self.download_targets()] = {'resource': self.target_cfg.resource,
                                                                 'gs_output_dir' : self.gs_output_dir}
        list_files_ChEMBL_downloaded[self.download_mechanisms()] = {'resource': self.mechanism_cfg.resource,
                                                                    'gs_output_dir': self.gs_output_dir}
        list_files_ChEMBL_downloaded[self.download_protein_classification()] = {'resource': self.component_cfg.resource,
                                                                                'gs_output_dir': self.gs_output_dir}
        list_files_ChEMBL_downloaded[self.download_protein_class()] = {'resource': self.protein_cfg.resource,
                                                                       'gs_output_dir': self.gs_output_dir}
        return list_files_ChEMBL_downloaded

    def compress_ChEMBL_files(self, files_unzipped):
        """
        Compresses each file in files_unzipped using gzip algorithm and returns dictionary of filename -> {
        resource: ..., gs_output_dir: ...
        """
        zipped_files = {}
        for file_with_path in files_unzipped:
            filename_zip = make_gzip(file_with_path)
            zipped_files[filename_zip] = {'resource': files_unzipped[file_with_path]['resource'],
                                          'gs_output_dir': self.gs_output_dir}
        return zipped_files

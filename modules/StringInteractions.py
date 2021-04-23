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
        self.yaml = yaml_dict
        self.string_url = yaml_dict.string_info.uri
        self.string_info = yaml_dict.string_info
        self.ensembl_gtf_url = yaml_dict.string_info.additional_resouces.ensembl_ftp
        self.network_json_schema_url = yaml_dict.string_info.additional_resouces.network_json_schema.url
        self.output_string = yaml_dict.string_info.output_string
        self.output_protein_mapping = yaml_dict.string_info.additional_resouces.ensembl_ftp.output_protein_mapping
        self.list_files_downloaded = {}


    def getStringResources(self):
        # Fetch string network data and generate evidence json:
        ensembl_protein_mapping = self.get_ensembl_protein_mapping()
        self.list_files_downloaded[ensembl_protein_mapping] = {'resource': self.ensembl_gtf_url.resource,
                                                      'gs_output_dir': self.gs_output_dir }

        string_file = self.download.execute_download(self.string_info)
        self.list_files_downloaded[string_file] = {'resource': self.yaml.string_info.resource,
                                                  'gs_output_dir': self.gs_output_dir }

        return self.list_files_downloaded


    def get_ensembl_protein_mapping(self):
        ensembl_file = self.download.ftp_download(self.ensembl_gtf_url)
        return ensembl_file

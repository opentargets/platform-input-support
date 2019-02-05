import logging
import os
import yaml

from definitions import ROOT_DIR, PIS_OUTPUT_DIR
from DownloadResource import DownloadResource
from modules.common.YAMLReader import YAMLReader
from addict import Dict
import collections

logger = logging.getLogger(__name__)


class DataPipelineConfig(object):
    def __init__(self, yaml_dict, output_dir = PIS_OUTPUT_DIR):
        self.data_pipeline_uri = yaml_dict.uri
        self.output_filename = yaml_dict.output_filename if 'output_filename' in yaml_dict else 'mrtarget.data.yml'
        self.output_dir = output_dir

    def open_config_file(self):
        filename = self.output_dir + '/' + self.output_filename
        if os.path.exists(filename): os.remove(filename)
        conf_file = open(filename, "a+")
        return conf_file

    def download_template_schema(self):
        download = DownloadResource(self.output_dir)
        resource_info = Dict({'uri': self.data_pipeline_uri, 'output_filename': 'template.mrtarget.data.yml'})
        destination_filename = download.execute_download(resource_info)
        return destination_filename

    def create_config_file(self, list_files):
        logging.info("Creating data pipeline config file.")
        data_pipeline_schema = self.download_template_schema()
        data_pipeline_yaml = YAMLReader(data_pipeline_schema)
        data_pipeline_config=data_pipeline_yaml.read_yaml(True)
        conf_file = self.open_config_file()
        list_resources = {}
        for k, v in list_files.items():
            list_resources.setdefault(v, []).append(k)

        for k,v in list_resources.items():
            if k in data_pipeline_config:
               data_pipeline_config[k] = v

        with self.open_config_file() as outfile:
            yaml.safe_dump(data_pipeline_config, outfile,default_flow_style=False, allow_unicode=True)

        logging.info("Data Pipeline YAML file created.")
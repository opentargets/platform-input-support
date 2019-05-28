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
        self.output_filename = yaml_dict.output_filename if 'output_filename' in yaml_dict else 'partial.mrtarget.data.yml'
        self.output_dir = output_dir

    def open_config_file(self, prefix_file=None):
        filename = prefix_file + self.output_filename if prefix_file is not None else self.output_filename
        filename_path = self.output_dir + '/' + filename
        if os.path.exists(filename_path): os.remove(filename_path)
        conf_file = open(filename_path, "a+")
        return conf_file

    def download_template_schema(self):
        download = DownloadResource(self.output_dir)
        resource_info = Dict({'uri': self.data_pipeline_uri, 'output_filename': 'template.mrtarget.data.yml'})
        destination_filename = download.execute_download(resource_info)
        return destination_filename

    def create_config_file(self, list_files, prefix_file = None):
        logging.info("Creating data pipeline config file.")
        data_pipeline_schema = self.download_template_schema()
        data_pipeline_yaml = YAMLReader(data_pipeline_schema)
        data_pipeline_config=data_pipeline_yaml.read_yaml(True)
        list_resources = {}
        for k, v in list_files.items():
            list_resources.setdefault(v['resource'], []).append(k)

        for k,v in list_resources.items():
            if k in data_pipeline_config:
                if (len(v) == 1) and isinstance(data_pipeline_config[k], basestring):
                    data_pipeline_config[k] = v[0]
                else:
                    data_pipeline_config[k] = v
            else:
                logging.error("The key %s does not exist", k)

        with self.open_config_file(prefix_file) as outfile:
            yaml.safe_dump(data_pipeline_config, outfile,default_flow_style=False, allow_unicode=True)

        logging.info("Data Pipeline YAML file created.")

    def get_keys_config_file(self):
        logging.info("List of keys config file")
        data_pipeline_schema = self.download_template_schema()
        data_pipeline_yaml = YAMLReader(data_pipeline_schema)
        data_pipeline_config=data_pipeline_yaml.read_yaml(True)

        return data_pipeline_config.keys()

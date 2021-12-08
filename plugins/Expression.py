import logging
from yapsy.IPlugin import IPlugin
from modules.common import make_unzip_single_file, make_gzip
from modules.common import create_output_dir
from modules.common.Downloads import Downloads
from opentargets_urlzsource import URLZSource
import jsonlines
import json
import datetime
import os

logger = logging.getLogger(__name__)

"""

"""
class Expression(IPlugin):
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')

    def save_tissue_translation_map(self, output_path, resource, filename):
        tissues_json = {}
        with URLZSource(filename).open(mode='rb') as r_file:
            tissues_json['tissues'] = json.load(r_file)['tissues']
        r_file.close()
        create_output_dir(os.path.join(output_path, resource.path))
        filename_tissue = os.path.join(output_path, resource.path, resource.output_filename.replace('{suffix}', self.suffix))
        with jsonlines.open(filename_tissue, mode='w') as writer:
            for item in tissues_json['tissues']:
                entry = {k: v for k, v in tissues_json['tissues'][item].items()}
                entry['tissue_id'] = item
                writer.write(entry)

    def get_tissue_map(self, output, resource):
        filename = Downloads.dowload_staging_http(output.staging_dir, resource)
        self.save_tissue_translation_map(output.prod_dir, resource, filename)

    def get_normal_tissues(self, output, resource):
        filename = Downloads.dowload_staging_http(output.staging_dir, resource)
        filename_unzip=make_unzip_single_file(filename)
        gzip_filename=os.path.join(create_output_dir(os.path.join(output.prod_dir, resource.path)),resource.output_filename.replace('{suffix}', self.suffix))
        make_gzip(filename_unzip, gzip_filename)

    def process(self, conf, output, cmd_conf):
        self._logger.info("Expression step")
        Downloads(output.prod_dir).exec(conf)

        self.get_tissue_map(output, conf.etl.tissue_translation_map)
        self.get_normal_tissues(output, conf.etl.normal_tissues)


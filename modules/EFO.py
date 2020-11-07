import datetime
import logging
from definitions import PIS_OUTPUT_EFO, PIS_OUTPUT_ANNOTATIONS
from .DownloadResource import DownloadResource
import subprocess
import errno
import os
import shutil

logger = logging.getLogger(__name__)


class EFO(object):

    def __init__(self, yaml):
        self.yaml = yaml
        self.output_dir = PIS_OUTPUT_ANNOTATIONS
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.gs_save_original_files_dir = yaml.gs_output_dir + '/efo_owl'
        self.list_files_downloaded = {}
        self.riot_cmd = shutil.which('riot')
        self.jq_cmd = shutil.which('jq')


    def riot(self, owl_file, json_file, owl_jq):
        jsonwrite = open(PIS_OUTPUT_ANNOTATIONS + '/' + json_file, "wb")
        try:
            riotp = subprocess.Popen([self.riot_cmd, "--output", "JSON-LD", owl_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            jqp = subprocess.Popen(["jq", "-r", owl_jq], stdin=riotp.stdout, stdout=subprocess.PIPE)
            jsonwrite.write(jqp.stdout.read())
            jsonwrite.close()
        except OSError as e:
            if e.errno == errno.ENOENT:
                # handle file not found error.
                logger.error(errno.ENOENT)
            else:
                # Something else went wrong
                raise

        return jsonwrite.name


    def convert_owl_to_jsonld(self, owl_file,owl_qj):
        head, tail = os.path.split(owl_file)
        json_file = tail.replace(".owl", ".json")
        return self.riot(owl_file, json_file, owl_qj)


    def download_owl(self, yaml_info):
        for entry in yaml_info:
            download = DownloadResource(PIS_OUTPUT_EFO)
            destination_filename = download.execute_download(entry)
            self.list_files_downloaded[destination_filename] = {'resource': entry.resource,
                                                                'gs_output_dir': self.gs_save_original_files_dir}
            json_filename = self.convert_owl_to_jsonld(destination_filename, entry.owl_jq)
            self.list_files_downloaded[json_filename] = {'resource': entry.resource,
                                                            'gs_output_dir': self.gs_output_dir}


    def generate_efo(self):
        logger.info("EFO process")
        self.download_owl(self.yaml.disease_phenotypes_downloads)
        self.download_owl(self.yaml.efo_downloads)


        return self.list_files_downloaded



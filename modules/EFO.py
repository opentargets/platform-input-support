import datetime
import logging
from definitions import PIS_OUTPUT_EFO, PIS_OUTPUT_ANNOTATIONS
from .DownloadResource import DownloadResource
from .helpers.EFO import EFO as Disease
import subprocess
import errno
import os
import shutil

logger = logging.getLogger(__name__)


class EFO(object):

    def __init__(self, yaml):
        self.yaml = yaml
        self.output_dir = yaml.gs_output_dir
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.gs_save_json_dir = yaml.gs_output_dir + '/efo_json'
        self.list_files_downloaded = {}
        #self.riot_cmd = shutil.which('riot')
        self.riot_cmd = '/home/cinzia/apache-jena/bin/riot'
        self.jq_cmd = shutil.which('jq')
        self.efo_json = None


    def riot(self, owl_file, json_file, owl_jq):
        jsonwrite = open(PIS_OUTPUT_EFO + '/' + json_file, "wb")
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
            download = DownloadResource(PIS_OUTPUT_ANNOTATIONS)
            destination_filename = download.execute_download(entry)
            self.list_files_downloaded[destination_filename] = {'resource': entry.resource,
                                                                'gs_output_dir': self.output_dir}
            json_filename = self.convert_owl_to_jsonld(destination_filename, entry.owl_jq)
            self.list_files_downloaded[json_filename] = {'resource': None,
                                                            'gs_output_dir': self.gs_save_json_dir}
            if entry.resource == 'ontology-efo':
                self.efo_json = json_filename

    def generate_efo(self):
        #logger.info("===> EFO-ECO: riot path: "+ self.riot_cmd)
        logger.info("===> EFO-ECO: JQ path: " + self.jq_cmd)
        #self.download_owl(self.yaml.disease_phenotypes_downloads)
        #self.download_owl(self.yaml.efo_downloads)
        #self.download_owl(self.yaml.eco_downloads)
        self.efo_json='/home/cinzia/gitRepositories/platform-input-support/output/annotation-files/efo/efo_otar_slim_v3.24.0.json'
        diseases = Disease(self.efo_json)
        diseases.generate()
        diseases.create_paths()
        diseases.save_diseases()

        return self.list_files_downloaded



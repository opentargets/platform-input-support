import logging
from addict import Dict
from definitions import PIS_OUTPUT_EFO, PIS_OUTPUT_ANNOTATIONS
from .DownloadResource import DownloadResource
from .helpers.EFO import EFO as Disease
from .helpers.HPOPhenotypes import HPOPhenotypes
from .common.Riot import Riot

logger = logging.getLogger(__name__)


class EFO(object):

    def __init__(self, yaml):
        self.yaml = yaml
        self.local_output_dir = PIS_OUTPUT_ANNOTATIONS
        self.output_dir = yaml.gs_output_dir
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

    def download_file(self, entry):
        download = DownloadResource(self.local_output_dir)
        destination_filename = download.execute_download(entry)
        self.list_files_downloaded[destination_filename] = {'resource': entry.resource,
                                                            'gs_output_dir': self.output_dir}
        return destination_filename


    # as_original
    def download_file_original(self, uri):
        entry = Dict()
        entry.uri = uri
        entry.output_filename = uri[uri.rfind("/") + 1:]
        download = DownloadResource(self.local_output_dir)
        destination_filename = download.execute_download(entry)

        return destination_filename

    def convert_owl(self, destination_filename, riot_cmd):
        json_filename = self.convert_owl_to_jsonld(destination_filename, riot_cmd)
        self.list_files_downloaded[json_filename] = {'resource': None,
                                                     'gs_output_dir': self.gs_save_json_dir}
        return json_filename

    def download_extra_files(self,yaml):
        for entry in yaml:
            download = DownloadResource(self.local_output_dir)
            destination_filename = download.execute_download(entry)
            self.list_files_downloaded[destination_filename] = {'resource': entry.resource,
                                                                'gs_output_dir': self.output_dir}
        return destination_filename

    def download_efo(self, yaml_info):
        downloaded_file= self.download_file_original(yaml_info.uri)
        self.list_files_downloaded[downloaded_file] = {'resource': yaml_info.resource,
                                                            'gs_output_dir': self.output_dir}
        efo_filename = self.convert_owl(downloaded_file, yaml_info.owl_jq)
        return efo_filename

    def generate_efo(self):
        logger.info("--- JQ path: --- " + self.jq_cmd)
        hpo_pheno_filename = self.download_file_original(self.yaml.hpo_phenotypes.uri)
        self.list_files_downloaded[hpo_pheno_filename] = {'resource': None,
                                                          'gs_output_dir': self.output_dir}
        efo_filename = self.download_efo(self.yaml.efo_downloads)
        #Potentially obsolete soon!
        self.download_extra_files(self.yaml.efo_extra_downloads)


        #hpo_pheno_filename = '/home/cinzia/gitRepositories/platform-input-support/output/annotation-files/hpo-phenotypes-2020-11-26.hpoa'
        #efo_filename = '/home/cinzia/gitRepositories/platform-input-support/output/annotation-files/efo/efo_otar_slim_v3.24.0.json'

        diseases = Disease(efo_filename)
        diseases.generate()
        hpo_phenotypes = HPOPhenotypes(hpo_pheno_filename)
        hpo_phenotypes.run(self.yaml.hpo_phenotypes.output_filename)
        diseases.create_paths()
        diseases.save_diseases()

        return self.list_files_downloaded



import logging
from modules.OpenFDA import OpenFDA
from .DownloadResource import DownloadResource
from .GoogleBucketResource import GoogleBucketResource
from .EnsemblResource import EnsemblResource
from .ChemicalProbesResource import ChemicalProbesResource
from .Drug import Drug
from .Homologues import Homologues
from .KnownTargetSafetyResource import KnownTargetSafetyResource
from .TEP import TEP
from .EFO import EFO
from .ECO import ECO
from .HPA import HPA
from .Interactions import Interactions
from .StringInteractions import StringInteractions
from definitions import *
from .DataPipelineConfig import DataPipelineConfig
from .common import get_lines, make_unzip_single_file, init_output_dirs, get_output_dir
import time


logger = logging.getLogger(__name__)

class RetrieveResource(object):

    def __init__(self, args, yaml, yaml_data_pipeline_schema):
        self.args = args
        self.output_dir = PIS_OUTPUT_DIR
        self.yaml = yaml
        self.yaml_data_pipeline_schema = yaml_data_pipeline_schema
        self.list_files_downloaded = {}
        self.list_google_storage_files = {}
        self.list_files_downladed_failed = {}

    def has_step(self, step):
        if self.args.exclude is not None:
            if step in self.args.exclude: return False
        if self.args.steps is None: return True
        if step in self.args.steps: return True
        return False

    def annotations_downloaded_by_uri(self):
        for entry in self.yaml.annotations.downloads:
            download = DownloadResource(PIS_OUTPUT_ANNOTATIONS)
            download.replace_suffix(self.args)
            if self.args.thread:
                destination_filename = download.execute_download_threaded(entry)
            else:
                destination_filename = download.execute_download(entry)

            if destination_filename is not None:
                if 'unzip_file' in entry:
                    destination_filename = make_unzip_single_file(destination_filename)

                self.list_files_downloaded[destination_filename] = { 'resource' : entry.resource,
                                                                      'gs_output_dir': self.yaml.annotations_from_buckets.gs_output_dir }
                logger.info("Files downloaded: %s", destination_filename)
            elif not self.args.skip:
                 raise ValueError("Error during downloading: {}", entry.uri)

        logger.info("Number of resources requested / Number of files downloaded: %s / %s",
                    len(self.yaml.annotations.downloads), len(self.list_files_downloaded))

    def get_efo(self):
        efo_resource = EFO(self.yaml.efo, self.yaml.config)
        list_files_efo = efo_resource.generate_efo()
        self.list_files_downloaded.update(list_files_efo)

    def get_eco(self):
        eco_resource = ECO(self.yaml.eco, self.yaml.config)
        list_files_eco = eco_resource.download_eco()
        self.list_files_downloaded.update(list_files_eco)

    def get_ensembl(self):
        ensembl_resource = EnsemblResource(self.yaml.ensembl)
        ensembl_filename = ensembl_resource.execute()
        self.list_files_downloaded[ensembl_filename] = {'resource': self.yaml.ensembl.resource, 'gs_output_dir': self.yaml.ensembl.gs_output_dir}

    def get_chemical_probes(self):
        # config.yaml chemical probes file : downnload spreadsheets + generate file for data_pipeline
        chemical_probes_resource = ChemicalProbesResource(PIS_OUTPUT_ANNOTATIONS)
        chemical_probes_resource.download_spreadsheet(self.yaml.chemical_probes,PIS_OUTPUT_CHEMICAL_PROBES)
        chemical_filename = chemical_probes_resource.generate_probes(self.yaml.chemical_probes)
        self.list_files_downloaded[chemical_filename] = {'resource': self.yaml.chemical_probes.resource,
                                                         'gs_output_dir': self.yaml.chemical_probes.gs_output_dir}

    # config.yaml known target safety file : download spreadsheets + generate file for data_pipeline
    def get_known_target_safety(self):
        known_target_safety_resource = KnownTargetSafetyResource(PIS_OUTPUT_ANNOTATIONS)
        known_target_safety_resource.download_spreadsheet(self.yaml.known_target_safety,PIS_OUTPUT_KNOWN_TARGET_SAFETY)
        ksafety_filename = known_target_safety_resource.generate_known_safety_json(self.yaml.known_target_safety)
        self.list_files_downloaded[ksafety_filename] = {'resource': self.yaml.known_target_safety.resource,
                                                         'gs_output_dir': self.yaml.known_target_safety.gs_output_dir}

    # config.yaml tep : download spreadsheets + generate file for ETL
    def get_TEP(self):
        tep_resource = TEP(PIS_OUTPUT_ANNOTATIONS)
        tep_resource.download_spreadsheet(self.yaml.tep, PIS_OUTPUT_TEP)
        tep_filename = tep_resource.generate_tep_json(self.yaml.tep)
        self.list_files_downloaded[tep_filename] = {'resource': self.yaml.tep.resource,
                                                    'gs_output_dir': self.yaml.tep.gs_output_dir}


    def get_interactions(self):
        # Intact Resource
        intact_resource = Interactions(self.yaml.interactions)
        list_files_intact = intact_resource.getIntactResources()
        self.list_files_downloaded.update(list_files_intact)
        # String resource
        string_resource = StringInteractions(self.yaml.interactions)
        list_files_string = string_resource.getStringResources()
        self.list_files_downloaded.update(list_files_string)

    def get_homologues(self):
        homologues = Homologues(self.yaml.homologies, self.yaml.config.jq)

        homology_files = homologues.download_resources()

        self.list_files_downloaded.update(homology_files)

    def get_drug(self):
        """
        Retrieves all resources specified in the `config.yaml` `drug` section and updates the `list_files_downloaded`
        with details of retrieved resources.
        """
        drug = Drug(self.yaml.drug)
        files = drug.get_all()
        self.list_files_downloaded.update(files)

    def get_file_from_bucket(self, entry, output, gs_output_dir):
        param = GoogleBucketResource.get_bucket_and_path(entry.bucket)
        google_resource = GoogleBucketResource(bucket_name=param)
        bucket = google_resource.get_bucket()
        list_files_bucket = {}
        if bucket is not None:
            latest_filename_info = google_resource.get_latest_file(entry)
            print(latest_filename_info)
            if not latest_filename_info["spark"]:
                if latest_filename_info["latest_filename"] is not None:
                    final_filename = google_resource.download_file_helper(output, entry.output_filename,
                                                                    latest_filename_info)
                    self.list_files_downloaded[final_filename] = {'resource': entry.resource,
                                                                  'gs_output_dir': gs_output_dir}
                    # fill in a specific variable for just evidence step.
                    list_files_bucket[final_filename] = entry.resource
                else:
                    logger.info(
                        "ERROR: The path={} does not contain any recent file".format(google_resource.get_bucket_name()))
                    if not self.args.skip:
                       raise ValueError("ERROR: The path={} does not contain any recent file".format(
                           google_resource.get_bucket_name()))
            else:
                #spark:
                dir_name = entry.output_spark_dir.replace('{suffix}', latest_filename_info["suffix"])
                output_dir = PIS_OUTPUT_EVIDENCES+'/'+ dir_name
                get_output_dir(None, output_dir)
                list_files_dir = google_resource.download_dir(latest_filename_info["latest_filename"],output_dir)
                for spark_filename in list_files_dir:
                    self.list_files_downloaded[spark_filename] = {'resource': entry.resource,
                                                                  'gs_output_dir': gs_output_dir+'/'+dir_name}
                    list_files_bucket[spark_filename] = entry.resource
        else:
            self.list_files_downladed_failed[google_resource.get_bucket_name()] = entry.resource
            logger.info("ERROR: Google Cloud Storage, path={}".format(google_resource.get_bucket_name()))
            if not self.args.skip:
                raise ValueError("ERROR: Google Cloud Storage, path={}".format(google_resource.get_bucket_name()))

        del google_resource
        return list_files_bucket


    def get_annotations_from_bucket(self):
        GoogleBucketResource.has_valid_auth_key(self.args.google_credential_key)
        for entry in self.yaml.annotations_from_buckets.downloads:
            self.get_file_from_bucket(entry, PIS_OUTPUT_ANNOTATIONS ,self.yaml.annotations_from_buckets.gs_output_dir)

    def get_hpa_expressions(self):
        # Retrieve info from google cloud bucket
        GoogleBucketResource.has_valid_auth_key(self.args.google_credential_key)
        for entry in self.yaml.hpa_from_buckets.downloads:
            self.get_file_from_bucket(entry, PIS_OUTPUT_ANNOTATIONS ,self.yaml.hpa_from_buckets.gs_output_dir)
        # Retrieve info from external resources
        hpa_resource = HPA(self.yaml.hpa, self.args)
        list_hpa_annotations = hpa_resource.get_hpa_annonations()
        self.list_files_downloaded.update(list_hpa_annotations)

    def get_evidences(self):
        GoogleBucketResource.has_valid_auth_key(self.args.google_credential_key)
        list_files_evidence = {}
        for entry in self.yaml.evidences.downloads:
            file_from_bucket = self.get_file_from_bucket(entry, PIS_OUTPUT_EVIDENCES, self.yaml.evidences.gs_output_dir)
            list_files_evidence.update(file_from_bucket)


        self.get_stats_files(list_files_evidence)

    def copy_files_to_google_storage(self):
        params = GoogleBucketResource.get_bucket_and_path(self.args.google_bucket)
        google_resource = GoogleBucketResource(bucket_name=params)
        for original_filename in self.list_files_downloaded:
            if 'is_a_dir' in self.list_files_downloaded[original_filename]:
                print("TODO")
            else:
                split_filename=original_filename.rsplit('/', 1)
                dest_filename = split_filename[1] if len(split_filename) == 2 else split_filename[0]
                bucket_filename=google_resource.copy_from(original_filename, dest_filename,
                                                      self.list_files_downloaded[original_filename]['gs_output_dir'])
                bucket_filename = GOOGLE_STORAGE_URI+google_resource.bucket_name+'/'+bucket_filename
                self.list_google_storage_files[bucket_filename] = self.list_files_downloaded[original_filename]

    def create_yaml_config_file(self):
        data_pipeline_config_file = DataPipelineConfig(self.yaml_data_pipeline_schema)
        if len(self.list_files_downloaded) > 0:
            data_pipeline_config_file.create_config_file_etl(self.list_google_storage_files,'etl.')
            data_pipeline_config_file.create_config_file(self.list_google_storage_files, 'gs.')
            data_pipeline_config_file.create_config_file(self.list_files_downloaded, 'local.')

    def get_stats_files(self, list_files):
        start = time.time()
        evidence_stats_file= os.path.join(PIS_OUTPUT_DIR, 'stats_evidence_files.csv')
        logger.info("Generating stats files: " + evidence_stats_file)
        if os.path.exists(evidence_stats_file): os.remove(evidence_stats_file)
        stats_file = open(evidence_stats_file, "a+")
        for original_filename in list_files:
            lines = get_lines(original_filename)
            filename_info = original_filename.rsplit('/', 1)[1]
            stats_file.write(filename_info + ',' + str(lines) + '\n')
        end=time.time()
        logging.info("Stats evidence file: time of execution {}".format(str(end - start)))

    def get_openfda(self):
        etlStep = OpenFDA(self.yaml.openfda)
        files = etlStep.run()
        self.list_files_downloaded.update(files)

    def run(self):
        google_opts = GoogleBucketResource.has_google_parameters(self.args.google_credential_key, self.args.google_bucket)
        if google_opts:
            GoogleBucketResource.has_valid_auth_key(self.args.google_credential_key)

        init_output_dirs()
        if self.has_step("annotations") : self.annotations_downloaded_by_uri()
        if self.has_step("annotations_from_buckets"): self.get_annotations_from_bucket()
        if self.has_step("hpa"): self.get_hpa_expressions()
        if self.has_step("chemical_probes"): self.get_chemical_probes()
        if self.has_step("drug"): self.get_drug()
        if self.has_step("efo"): self.get_efo()
        if self.has_step("eco"): self.get_eco()
        if self.has_step("ensembl"): self.get_ensembl()
        if self.has_step("evidence"): self.get_evidences()
        if self.has_step("interactions"): self.get_interactions()
        if self.has_step("homologues"): self.get_homologues()
        if self.has_step("known_target_safety"): self.get_known_target_safety()
        if self.has_step("tep"): self.get_TEP()
        if self.has_step("openfda"): self.get_openfda()

        # At this point the auth key is already valid.
        print(self.list_files_downloaded)
        if google_opts: self.copy_files_to_google_storage()

        self.create_yaml_config_file()

        logging.info("Done.")
        return True

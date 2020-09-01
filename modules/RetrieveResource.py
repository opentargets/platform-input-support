import logging
from common import get_output_dir
from DownloadResource import DownloadResource
from GoogleBucketResource import GoogleBucketResource
from EnsemblCondaResource import EnsemblCondaResource
from ChEMBL import ChEMBLLookup
from ChemicalProbesResource import ChemicalProbesResource
from KnownTargetSafetyResource import KnownTargetSafetyResource
from TEP import TEP
from Networks import Networks
from definitions import *
from DataPipelineConfig import DataPipelineConfig
from EvidenceSubset import EvidenceSubset
from AnnotationQC import AnnotationQC
from common import get_lines, make_unzip_single_file
import time

logger = logging.getLogger(__name__)

class RetrieveResource(object):

    def __init__(self,args, yaml, yaml_data_pipeline_schema):
        self.args = args
        self.output_dir = get_output_dir(args.output_dir, PIS_OUTPUT_DIR)
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
        output_dir_annotations = get_output_dir(None, PIS_OUTPUT_ANNOTATIONS)
        for entry in self.yaml.annotations.downloads:
            download = DownloadResource(output_dir_annotations)
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

    def get_ensembl(self):
        ensembl_resource = EnsemblCondaResource(self.yaml.ensembl)
        ensembl_filename = ensembl_resource.create_genes_dictionary()
        self.list_files_downloaded[ensembl_filename] = {'resource': self.yaml.ensembl.resource, 'gs_output_dir': self.yaml.ensembl.gs_output_dir}

    def get_chemical_probes(self):
        output_dir_annotations = get_output_dir(None, PIS_OUTPUT_ANNOTATIONS)
        # config.yaml chemical probes file : downnload spreadsheets + generate file for data_pipeline
        chemical_output_dir = get_output_dir(None, PIS_OUTPUT_CHEMICAL_PROBES)
        chemical_probes_resource = ChemicalProbesResource(output_dir_annotations)
        chemical_probes_resource.download_spreadsheet(self.yaml.chemical_probes,chemical_output_dir)
        chemical_filename = chemical_probes_resource.generate_probes(self.yaml.chemical_probes)
        self.list_files_downloaded[chemical_filename] = {'resource': self.yaml.chemical_probes.resource,
                                                         'gs_output_dir': self.yaml.chemical_probes.gs_output_dir}

    def get_known_target_safety(self):
        output_dir_annotations = get_output_dir(None, PIS_OUTPUT_ANNOTATIONS)
        # config.yaml known target safety file : download spreadsheets + generate file for data_pipeline
        safety_output_dir = get_output_dir(None, PIS_OUTPUT_KNOWN_TARGET_SAFETY)
        known_target_safety_resource = KnownTargetSafetyResource(output_dir_annotations)
        known_target_safety_resource.download_spreadsheet(self.yaml.known_target_safety,safety_output_dir)
        ksafety_filename = known_target_safety_resource.generate_known_safety_json(self.yaml.known_target_safety)
        self.list_files_downloaded[ksafety_filename] = {'resource': self.yaml.known_target_safety.resource,
                                                         'gs_output_dir': self.yaml.known_target_safety.gs_output_dir}

    def get_TEP(self):
        output_dir_annotations = get_output_dir(None, PIS_OUTPUT_ANNOTATIONS)
        # config.yaml tep : download spreadsheets + generate file for ETL
        tep_output_dir = get_output_dir(None, PIS_OUTPUT_TEP)
        tep_resource = TEP(output_dir_annotations)
        tep_resource.download_spreadsheet(self.yaml.tep, tep_output_dir)
        tep_filename = tep_resource.generate_tep_json(self.yaml.tep)
        self.list_files_downloaded[tep_filename] = {'resource': self.yaml.tep.resource,
                                                    'gs_output_dir': self.yaml.tep.gs_output_dir}


    def get_Networks(self):
        output_dir_annotations = get_output_dir(None, PIS_OUTPUT_ANNOTATIONS)
        output_dir_networks = get_output_dir(None, PIS_OUTPUT_NETWORK)
        network_resource = Networks(self.yaml.network)
        ensembl_info_filename = network_resource.download_ensembl()
        self.list_files_downloaded[ensembl_info_filename] = {'resource': None,
                                                            'gs_output_dir': self.yaml.network.gs_output_dir}
        intact_info_filename = network_resource.get_intact_info_file()
        self.list_files_downloaded[intact_info_filename] = {'resource': None,
                                                            'gs_output_dir': self.yaml.network.gs_output_dir}
        list_files_intact=network_resource.get_rna_central()
        for intact_filename in list_files_intact:
            self.list_files_downloaded[intact_filename] = {'resource': None,
                                                       'gs_output_dir': self.yaml.network.gs_output_dir+'/rna-central'}
        list_files_human=network_resource.get_uniprot_info_file()
        for human_filename in list_files_human:
            self.list_files_downloaded[human_filename] = {'resource': None,
                                                       'gs_output_dir': self.yaml.etwork.gs_output_dir+'/human-mapping'}
        # Here add the second file. String.

    # config.yaml ChEMBL REST API
    def get_ChEMBL(self):
        """
        Retrieves ChEMBL resources from both REST API and Elasticsearch instance as configured in `config.xml` and
        updates list_files_downloaded with downloaded ChEMBL files.
        """
        chembl_handler = ChEMBLLookup(self.yaml.ChEMBL)
        # standard files
        list_files_ChEMBL_unzipped = chembl_handler.download_chEMBL_resources()
        # compressed files (.gz)
        list_files_ChEMBL = chembl_handler.compress_ChEMBL_files(list_files_ChEMBL_unzipped)

        self.list_files_downloaded.update(list_files_ChEMBL)



    def get_file_from_bucket(self, entry, output, gs_output_dir):
        param = GoogleBucketResource.get_bucket_and_path(entry.bucket)
        google_resource = GoogleBucketResource(bucket_name=param)
        bucket = google_resource.get_bucket()
        list_files_bucket = {}
        subset_field = None if 'subset_key' not in entry else entry.subset_key
        subset_prefix = None if 'subset_prefix' not in entry else entry.subset_prefix
        if bucket is not None:
            latest_filename_info = google_resource.get_latest_file(entry)
            if latest_filename_info["latest_filename"] is not None:
                final_filename = google_resource.download_file_helper(output, entry.output_filename,
                                                               latest_filename_info)
                self.list_files_downloaded[final_filename] = {'resource': entry.resource,
                                                              'gs_output_dir': gs_output_dir,
                                                              'subset_key': subset_field,
                                                              'subset_prefix': subset_prefix}
                # fill in a specific variable for just evidence step.
                list_files_bucket[final_filename] = entry.resource
            else:
                logger.info(
                    "ERROR: The path={} does not contain any recent file".format(google_resource.get_bucket_name()))
                if not self.args.skip:
                    raise ValueError("ERROR: The path={} does not contain any recent file".format(
                        google_resource.get_bucket_name()))
        else:
            self.list_files_downladed_failed[google_resource.get_bucket_name()] = entry.resource
            logger.info("ERROR: Google Cloud Storage, path={}".format(google_resource.get_bucket_name()))
            if not self.args.skip:
                raise ValueError("ERROR: Google Cloud Storage, path={}".format(google_resource.get_bucket_name()))

        del google_resource
        return list_files_bucket

    def get_annotations_from_bucket(self):
        output_dir_annotations = get_output_dir(None, PIS_OUTPUT_ANNOTATIONS)
        GoogleBucketResource.has_valid_auth_key(self.args.google_credential_key)
        for entry in self.yaml.annotations_from_buckets.downloads:
            self.get_file_from_bucket(entry, output_dir_annotations ,self.yaml.annotations_from_buckets.gs_output_dir)

    def get_evidences(self):
        GoogleBucketResource.has_valid_auth_key(self.args.google_credential_key)
        output_dir_evidence = get_output_dir(None, PIS_OUTPUT_EVIDENCES)
        list_files_evidence = {}
        for entry in self.yaml.evidences.downloads:
            file_from_bucket = self.get_file_from_bucket(entry, output_dir_evidence, self.yaml.evidences.gs_output_dir)
            list_files_evidence.update(file_from_bucket)


        self.get_stats_files(list_files_evidence)
        output_dir_subset = get_output_dir(None, PIS_OUTPUT_SUBSET_EVIDENCES)
        subsetEvidence = EvidenceSubset(ROOT_DIR+'/minimal_ensembl.txt',output_dir_subset,self.yaml.evidences.gs_output_dir)
        list_files_subsets = subsetEvidence.execute_subset(self.list_files_downloaded)
        subsetEvidence.create_stats_file()
        self.list_files_downloaded.update(list_files_subsets)

    def annotations_qc(self, google_opts):
        if not google_opts:
            logging.error("The Annotation QC step requires Google Cloud credential")
        else:
            output_dir_qc = get_output_dir(None, PIS_OUTPUT_ANNOTATIONS_QC)
            datatype_qc = AnnotationQC(self.yaml.annotations_qc, self.list_files_downloaded, output_dir_qc)
            list_files_downloaded = datatype_qc.execute()
            self.list_files_downloaded.update(list_files_downloaded)

    def copy_files_to_google_storage(self):
        params = GoogleBucketResource.get_bucket_and_path(self.args.google_bucket)
        google_resource = GoogleBucketResource(bucket_name=params)
        for original_filename in self.list_files_downloaded:
            if 'is_a_dir' in self.list_files_downloaded[original_filename]:
                print "TODO"
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
            data_pipeline_config_file.create_config_file(self.list_google_storage_files, 'gs.')
            data_pipeline_config_file.create_config_file(self.list_files_downloaded, 'local.')

    def get_stats_files(self, list_files):
        start = time.time()
        logger.info("Generating stats files: " + PIS_EVIDENCES_STATS_FILE)
        if os.path.exists(PIS_EVIDENCES_STATS_FILE): os.remove(PIS_EVIDENCES_STATS_FILE)
        stats_file = open(PIS_EVIDENCES_STATS_FILE, "a+")
        for original_filename in list_files:
            lines = get_lines(original_filename)
            filename_info = original_filename.rsplit('/', 1)[1]
            stats_file.write(filename_info + ',' + str(lines) + '\n')
        end=time.time()
        logging.info("Stats evidence file: time of execution {}".format(str(end - start)))

    def run(self):
        google_opts = GoogleBucketResource.has_google_parameters(self.args.google_credential_key, self.args.google_bucket)
        if google_opts:
            GoogleBucketResource.has_valid_auth_key(self.args.google_credential_key)

        if self.has_step("annotations") : self.annotations_downloaded_by_uri()
        if self.has_step("ensembl"): self.get_ensembl()
        if self.has_step("chemical_probes"): self.get_chemical_probes()
        if self.has_step("known_target_safety"): self.get_known_target_safety()
        if self.has_step("tep"): self.get_TEP()
        if self.has_step("networks"): self.get_Networks()
        if self.has_step("ChEMBL"): self.get_ChEMBL()
        if self.has_step("annotations_from_buckets"): self.get_annotations_from_bucket()
        if self.has_step("evidences"): self.get_evidences()
        if self.has_step("annotations_qc"): self.annotations_qc(google_opts)

        # At this point the auth key is already valid.
        print self.list_files_downloaded
        if google_opts: self.copy_files_to_google_storage()

        self.create_yaml_config_file()

        logging.info("Done.")
        return True

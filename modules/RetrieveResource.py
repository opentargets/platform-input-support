import logging
from common import get_output_dir
from DownloadResource import DownloadResource
from GoogleBucketResource import GoogleBucketResource
from EnsemblResource import EnsemblResource
from ChEMBL import ChEMBLLookup
from ChemicalProbesResource import ChemicalProbesResource
from definitions import *
from DataPipelineConfig import DataPipelineConfig
from common import get_lines, make_zip

logger = logging.getLogger(__name__)

class RetrieveResource(object):

    def __init__(self,args, yaml, yaml_data_pipeline_schema):
        self.args = args
        self.output_dir = get_output_dir(args.output_dir, PIS_OUTPUT_ANNOTATIONS)
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
            download = DownloadResource(self.output_dir)
            download.replace_suffix(self.args)
            if self.args.thread:
                destination_filename = download.execute_download_threaded(entry)
            else:
                destination_filename = download.execute_download(entry)

            if destination_filename is not None:
                 self.list_files_downloaded[destination_filename] = { 'resource' : entry.resource,
                                                                      'gs_output_dir': self.yaml.annotations_from_buckets.gs_output_dir }
            elif not self.args.skip:
                 raise ValueError("Error during downloading: {}", entry.uri)

        logger.info("Number of resources requested / Number of files downloaded: %s / %s",
                    len(self.yaml.annotations), len(self.list_files_downloaded))

    def get_ensembl(self):
        ensembl_resource = EnsemblResource(self.yaml.ensembl)
        ensembl_filename = ensembl_resource.create_genes_dictionary()
        self.list_files_downloaded[ensembl_filename] = {'resource': self.yaml.ensembl.resource, 'gs_output_dir': self.yaml.ensembl.gs_output_dir}

    def get_chemical_probes(self):
        # config.yaml chemical probes file : downnload spreadsheets + generate file for data_pipeline
        chemical_output_dir = get_output_dir(None, PIS_OUTPUT_CHEMICAL_PROBES)
        chemical_probes_resource = ChemicalProbesResource(self.output_dir)
        chemical_probes_resource.download_spreadsheet(self.yaml.chemical_probes,chemical_output_dir)
        chemical_filename = chemical_probes_resource.generate_probes(self.yaml.chemical_probes)
        self.list_files_downloaded[chemical_filename] = {'resource': self.yaml.chemical_probes.resource,
                                                         'gs_output_dir': self.yaml.chemical_probes.gs_output_dir}
    # config.yaml ChEMBL REST API
    def get_ChEMBL(self):
        list_files_ChEMBL ={}
        output_dir_ChEMBL = get_output_dir(None, PIS_OUTPUT_CHEMBL_API)
        chembl_handler = ChEMBLLookup(self.yaml.ChEMBL)
        list_files_ChEMBL_unzipped = chembl_handler.download_chEMBL_files()
        for file_with_path in list_files_ChEMBL_unzipped:
            filename_zip = make_zip(file_with_path)
            list_files_ChEMBL[filename_zip] = {'resource': list_files_ChEMBL_unzipped[file_with_path]['resource'],
                                               'gs_output_dir': self.yaml.ChEMBL.gs_output_dir }
        self.list_files_downloaded.update(list_files_ChEMBL)



    def get_file_from_bucket(self, entry, output, gs_output_dir):
        param = GoogleBucketResource.get_bucket_and_path(entry.bucket)
        google_resource = GoogleBucketResource(bucket_name=param)
        bucket = google_resource.get_bucket()
        list_files_bucket = {}
        if bucket is not None:
            latest_filename_info = google_resource.get_latest_file(entry)
            if latest_filename_info["latest_filename"] is not None:
                final_filename = google_resource.download_file(output, entry.output_filename,
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
            self.list_files_downladed_failed[google_resource.get_bucket_name()] = entry.resource
            logger.info("ERROR: Google Cloud Storage, path={}".format(google_resource.get_bucket_name()))
            if not self.args.skip:
                raise ValueError("ERROR: Google Cloud Storage, path={}".format(google_resource.get_bucket_name()))

        del google_resource
        return list_files_bucket

    def get_annotations_from_bucket(self):
        GoogleBucketResource.has_valid_auth_key(self.args.google_credential_key)
        for entry in self.yaml.annotations_from_buckets.downloads:
            self.get_file_from_bucket(entry, self.output_dir,self.yaml.annotations_from_buckets.gs_output_dir)

    def get_evidences(self):
        GoogleBucketResource.has_valid_auth_key(self.args.google_credential_key)
        output_dir_evidence = get_output_dir(None, PIS_OUTPUT_EVIDENCES)
        for entry in self.yaml.evidences.downloads:
            list_files_evidence = self.get_file_from_bucket(entry, output_dir_evidence, self.yaml.evidences.gs_output_dir)
        self.get_stats_files(list_files_evidence)

    def copy_files_to_google_storage(self):
        params = GoogleBucketResource.get_bucket_and_path(self.args.google_bucket)
        google_resource = GoogleBucketResource(bucket_name=params)
        for original_filename in self.list_files_downloaded:
            split_filename=original_filename.rsplit('/', 1)
            dest_filename = split_filename[1] if len(split_filename) == 2 else split_filename[0]
            bucket_filename=google_resource.copy_from(original_filename, dest_filename,
                                                      self.list_files_downloaded[original_filename]['gs_output_dir'])
            bucket_filename = GOOGLE_STORAGE_URI+bucket_filename
            self.list_google_storage_files[bucket_filename] = self.list_files_downloaded[original_filename]

    def create_yaml_config_file(self):
        data_pipeline_config_file = DataPipelineConfig(self.yaml_data_pipeline_schema)
        if len(self.list_files_downloaded) > 0:
            data_pipeline_config_file.create_config_file(self.list_google_storage_files, 'gs.')
            data_pipeline_config_file.create_config_file(self.list_files_downloaded, 'local.')

    def get_stats_files(self, list_files):
        logger.info("Generating stats files: " + PIS_EVIDENCES_STATS_FILE)
        if os.path.exists(PIS_EVIDENCES_STATS_FILE): os.remove(PIS_EVIDENCES_STATS_FILE)
        stats_file = open(PIS_EVIDENCES_STATS_FILE, "a+")
        for original_filename in list_files:
            lines = get_lines(original_filename)
            filename_info = original_filename.rsplit('/', 1)[1]
            stats_file.write(filename_info + ',' + str(lines) + '\n')

    def run(self):
        output_dir_annotations = get_output_dir(self.args.output_dir, PIS_OUTPUT_ANNOTATIONS)
        google_opts = GoogleBucketResource.has_google_parameters(self.args.google_credential_key, self.args.google_bucket)
        if google_opts:
            GoogleBucketResource.has_valid_auth_key(self.args.google_credential_key)

        if self.has_step("annotations") : self.annotations_downloaded_by_uri()
        if self.has_step("ensembl"): self.get_ensembl()
        if self.has_step("chemical_probes"): self.get_chemical_probes()
        if self.has_step("ChEMBL"): self.get_ChEMBL()
        if self.has_step("annotations_from_buckets"): self.get_annotations_from_bucket()
        if self.has_step("evidences"): self.get_evidences()

        # At this point the auth key is already valid.
        if google_opts: self.copy_files_to_google_storage()

        self.create_yaml_config_file()

        logging.info("Done.")
        return True

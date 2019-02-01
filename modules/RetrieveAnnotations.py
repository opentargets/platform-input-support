import sys

# Custom modules
import modules.cfg as cfg
from modules.DownloadResource import DownloadResource
from modules.GoogleBucketResource import GoogleBucketResource
from definitions import PIS_OUTPUT_ANNOTATIONS, PIS_OUTPUT_CHEMICAL_PROBES, PIS_OUTPUT_CHEMBL_API
from modules.common.YAMLReader import YAMLReader
from modules.ChemicalProbesResource import ChemicalProbesResource
from modules.EnsemblResource import EnsemblResource
from modules.ChEMBL import ChEMBLLookup
import logging

logger = logging.getLogger(__name__)

def annotations_downloaded_by_uri(args, yaml_dict, output_dir):
    list_files_downloaded = []

    for entry in yaml_dict:
        download = DownloadResource(output_dir)
        download.replace_suffix(args)
        if args.thread:
            destination_filename = download.execute_download_threaded(entry)
        else:
            destination_filename = download.execute_download(entry)

        if destination_filename is not None:
            list_files_downloaded.append(destination_filename)
        elif not args.skip:
                raise ValueError("Error during downloading: {}",entry.uri)

    return list_files_downloaded


def main():
    cfg.setup_parser()
    args = cfg.get_args()

    yaml = YAMLReader()
    yaml_dict = yaml.get_Dict()
    cfg.get_list_steps_on_request(args.list_steps,yaml.get_list_keys())

    cfg.set_up_logging(args)
    output_dir = cfg.get_output_dir(args.output_dir, PIS_OUTPUT_ANNOTATIONS)
    google_opts = GoogleBucketResource.has_google_parameters(args.google_credential_key, args.google_bucket)
    if google_opts:
        GoogleBucketResource.has_valid_auth_key(args.google_credential_key)

    list_files_downloaded = []

    if args.step is None or args.step == "annotations":
        list_files_downloaded = annotations_downloaded_by_uri(args, yaml_dict.annotations, output_dir)
        # Useful with the option --skip
        logger.info("Number of resources requested / Number of files downloaded: %s / %s",
                  len(yaml_dict.annotations), len(list_files_downloaded))

    if args.step is None or args.step == "ensembl":
        # config.yaml ensembl section
        ensembl_resource = EnsemblResource(yaml_dict.ensembl)
        ensembl_filename = ensembl_resource.create_genes_dictionary()
        list_files_downloaded.append(ensembl_filename)

    if args.step is None or args.step == "chemical_probes":
        # config.yaml chemical probes file : downnload spreadsheets + generate file for data_pipeline
        chemical_output_dir = cfg.get_output_dir(None, PIS_OUTPUT_CHEMICAL_PROBES)
        chemical_probes_resource = ChemicalProbesResource(output_dir)
        chemical_probes_resource.download_spreadsheet(yaml_dict,chemical_output_dir)
        chemical_filename = chemical_probes_resource.generate_probes(yaml_dict)
        list_files_downloaded.append(chemical_filename)

    if args.step is None or args.step == "ChEMBL":
        # config.yaml ChEMBL REST API
        output_dir_ChEMBL = cfg.get_output_dir(args.output_dir, PIS_OUTPUT_CHEMBL_API)
        chembl_handler = ChEMBLLookup(yaml_dict.ChEMBL)

        list_files_ChEMBL = chembl_handler.download_chEMBL_files()
        list_files_downloaded.extend(list_files_ChEMBL)

    if args.step is None or args.step == "annotations_from_buckets":
        GoogleBucketResource.has_valid_auth_key(args.google_credential_key)
        for entry in yaml_dict.annotations_from_buckets:
            param = GoogleBucketResource.get_bucket_and_path(entry.bucket)
            google_resource = GoogleBucketResource(bucket_name=param)
            bucket = google_resource.get_bucket()
            if bucket is not None:
                latest_filename_info = google_resource.get_latest_file(entry)
                final_filename = google_resource.download_file(output_dir, entry.output_filename, latest_filename_info)
                list_files_downloaded.append(final_filename)
            else:
                logger.info("ERROR: Google Cloud Storage, path={}".format(google_resource.get_bucket_name()))
                if not args.skip:
                    raise ValueError("ERROR: Google Cloud Storage, path={}".format(google_resource.get_bucket_name()))

        del google_resource

    # At this point the auth key is already valid.
    if google_opts:
        params = GoogleBucketResource.get_bucket_and_path(args.google_bucket)
        google_resource = GoogleBucketResource(bucket_name=params)
        for original_filename in list_files_downloaded:
            split_filename=original_filename.rsplit('/', 1)
            dest_filename = split_filename[1] if len(split_filename) == 2 else split_filename[0]
            google_resource.copy_from(original_filename, dest_filename)

        google_resource.list_blobs_object_path()


if __name__ == '__main__':
    sys.exit(main())
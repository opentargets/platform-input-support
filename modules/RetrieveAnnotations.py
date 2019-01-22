import sys

# Custom modules
import modules.cfg as cfg
from modules.DownloadResource import DownloadResource
from modules.GoogleSpreadSheet import GoogleSpreadSheet
from modules.GoogleBucketResource import GoogleBucketResource
from definitions import PIS_OUTPUT_ANNOTATIONS, PIS_OUTPUT_CHEMICAL_PROBES
from modules.common.YAMLReader import YAMLReader

def main():

    cfg.setup_parser()
    args = cfg.get_args()
    output_dir = cfg.get_output_dir(args.output_dir, PIS_OUTPUT_ANNOTATIONS)
    google_opts = GoogleBucketResource.has_google_parameters(args.google_credential_key, args.google_bucket)
    if google_opts:
        GoogleBucketResource.has_valid_auth_key(args.google_credential_key)

    list_files_downloaded = []
    yaml = YAMLReader()
    for entry in yaml.get_Dict().annotations:
        download = DownloadResource(output_dir)
        download.replace_suffix(args)
        if args.thread:
            destination_filename = download.execute_download_threaded(entry)
        else:
            destination_filename = download.execute_download(entry)

        list_files_downloaded.append(destination_filename)

    for spreadsheet_info in yaml.get_Dict().chemical_probes:
        output_dir = cfg.get_output_dir(None, PIS_OUTPUT_CHEMICAL_PROBES)
        google_spreedsheet = GoogleSpreadSheet(PIS_OUTPUT_CHEMICAL_PROBES)
        google_spreedsheet.download_as_csv(spreadsheet_info)

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
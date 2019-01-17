import sys

# Custom modules
import modules.cfg as cfg
from modules.DownloadResource import DownloadResource
from modules.GoogleBucketResource import GoogleBucketResource
from definitions import ROOT_DIR, OT_OUTPUT_DIR

def main():

    cfg.setup_parser()
    args = cfg.get_args()

    input_file = cfg.get_input_file(args.input_file, ROOT_DIR+'/annotations_input.csv')
    output_dir = cfg.get_output_dir(args.output_dir, OT_OUTPUT_DIR)
    google_opts = GoogleBucketResource.has_google_parameters(args.google_credential_key, args.google_bucket)
    if google_opts:
        GoogleBucketResource.has_valid_auth_key(args.google_credential_key)

    list_files_downloaded = []
    for file_to_download in cfg.get_list_of_file_download(input_file):
        download = DownloadResource(output_dir)
        download.replace_suffix(args)
        if args.thread:
            destination_filename = download.execute_download_threaded(file_to_download)
        else:
            destination_filename = download.execute_download(file_to_download)

        list_files_downloaded.append(destination_filename)

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
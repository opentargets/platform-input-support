import sys
import os
import logging.config

# Custom modules
import modules.cfg as cfg
from modules.GoogleBucketResource import GoogleBucketResource
from definitions import PIS_OUTPUT_EVIDENCES, PIS_EVIDENCES_STATS_FILE
from modules.common.YAMLReader import YAMLReader
from common import get_lines

logger = logging.getLogger(__name__)


def main():
    cfg.setup_parser()
    args = cfg.get_args()
    yaml = YAMLReader()
    yaml_dict = yaml.get_Dict()
    cfg.get_list_steps_on_request(args.list_steps,yaml.get_list_keys())
    cfg.set_up_logging(args)

    output_dir = cfg.get_output_dir(args.output_dir, PIS_OUTPUT_EVIDENCES)
    GoogleBucketResource.has_valid_auth_key(args.google_credential_key)

    list_files_downloaded = []
    list_files_downladed_failed = []
    for entry in yaml_dict.evidences:
        param = GoogleBucketResource.get_bucket_and_path(entry.bucket)
        google_resource = GoogleBucketResource(bucket_name=param)
        bucket = google_resource.get_bucket()
        if bucket is not None:
            latest_filename_info = google_resource.get_latest_file(entry)
            final_filename = google_resource.download_file(output_dir, entry.output_filename, latest_filename_info)
            list_files_downloaded.append(final_filename)
        else:
            list_files_downladed_failed.append(google_resource.get_bucket_name())
            logger.info("ERROR: Google Cloud Storage, path={}".format(google_resource.get_bucket_name()))
            if not args.skip:
                raise ValueError("ERROR: Google Cloud Storage, path={}".format(google_resource.get_bucket_name()))

        del google_resource

    if os.path.exists(PIS_EVIDENCES_STATS_FILE): os.remove(PIS_EVIDENCES_STATS_FILE)
    stats_file = open(PIS_EVIDENCES_STATS_FILE, "a+")
    for original_filename in list_files_downloaded:
        lines = get_lines(original_filename)
        stats_file.write(original_filename+','+str(lines)+'\n')

    # At this point the auth key is already valid.
    if args.google_bucket:
        params = GoogleBucketResource.get_bucket_and_path(args.google_bucket)
        google_resource = GoogleBucketResource(bucket_name=params)
        for original_filename in list_files_downloaded:
            split_filename=original_filename.rsplit('/', 1)
            dest_filename = split_filename[1] if len(split_filename) == 2 else split_filename[0]
            get_lines(original_filename)
            google_resource.copy_from(original_filename, dest_filename)

        google_resource.list_blobs_object_path()


if __name__ == '__main__':
    sys.exit(main())
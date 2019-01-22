import sys
import re
import os
import logging
import logging.config

# Custom modules
import modules.cfg as cfg
from modules.GoogleBucketResource import GoogleBucketResource
from datetime import datetime
from definitions import ROOT_DIR, OT_OUTPUT_DIR
from modules.common.YAMLReader import YAMLReader

logger = logging.getLogger(__name__)


def set_up_logging(args):
    #set up logging
    logger = None
    if args.log_config:
        if os.path.isfile(args.log_config) and os.access(args.log_config, os.R_OK):
            logging.config.fileConfig(args.log_config,  disable_existing_loggers=False)
            logger = logging.getLogger(__name__+".main()")
        else:
            logging.basicConfig()
            logger = logging.getLogger(__name__+".main()")
            logger.warning("unable to read file {}".format(args.log_config))

    else:
        logging.basicConfig()
        logger = logging.getLogger(__name__+".main()")

    if args.log_level:
        try:
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.getLevelName(args.log_level))
            logger.setLevel(logging.getLevelName(args.log_level))
            logger.info('main log level set to: '+ str(args.log_level))
            root_logger.info('root log level set to: '+ str(args.log_level))
        except Exception, e:
            root_logger.exception(e)
            return 1

def extract_latest_file(list_blobs):
    last_recent_file= None
    recent_date = datetime.strptime('01-01-1900', '%d-%m-%Y')
    for filename in list_blobs:
        find_date_file = re.search("([0-9]{2}\-[0-9]{2}\-[0-9]{4})", filename)
        if find_date_file:
            date_file = datetime.strptime(find_date_file.group(1), '%d-%m-%Y')
            if date_file > recent_date:
                recent_date = date_file
                last_recent_file = filename
    logger.info("Latest file: %s %s",last_recent_file, recent_date.strftime('%d-%m-%Y'))
    return {"latest_filename": last_recent_file,"suffix": recent_date.strftime('%d-%m-%Y')}


def get_latest_file(google_resource):
    list_blobs = google_resource.list_blobs_object_path()
    latest_filename_info = extract_latest_file(list_blobs)

    return latest_filename_info


def download_file(bucket, output_dir, output_filename, latest_filename_info):
    final_filename = output_dir + '/' + output_filename.replace('{suffix}',latest_filename_info["suffix"])
    blob = bucket.blob(latest_filename_info["latest_filename"])
    blob.download_to_filename(final_filename)

    return final_filename

def main():

    cfg.setup_parser()
    args = cfg.get_args()
    set_up_logging(args)

    output_dir = cfg.get_output_dir(args.output_dir, OT_OUTPUT_DIR)
    output_dir = output_dir+"/evidence_files"
    GoogleBucketResource.has_valid_auth_key(args.google_credential_key)


    list_files_downloaded = []
    list_files_downladed_failed = []
    yaml = YAMLReader()
    for entry in yaml.get_Dict().evidences:
        param = GoogleBucketResource.get_bucket_and_path(entry.bucket)
        google_resource = GoogleBucketResource(bucket_name=param)
        bucket = google_resource.get_bucket()
        if bucket is not None:
            latest_filename_info = get_latest_file(google_resource)
            final_filename = download_file(bucket, output_dir, entry.output_filename, latest_filename_info)
            list_files_downloaded.append(final_filename)
        else:
            list_files_downladed_failed.append(google_resource.get_bucket_name())
            logger.info("ERROR: Google Cloud Storage, path={}".format(google_resource.get_bucket_name()))
            if not args.skip:
                raise ValueError("ERROR: Google Cloud Storage, path={}".format(google_resource.get_bucket_name()))

        del google_resource

    # At this point the auth key is already valid.
    if args.google_bucket:
        params = GoogleBucketResource.get_bucket_and_path(args.google_bucket)
        google_resource = GoogleBucketResource(bucket_name=params)
        for original_filename in list_files_downloaded:
            split_filename=original_filename.rsplit('/', 1)
            dest_filename = split_filename[1] if len(split_filename) == 2 else split_filename[0]
            google_resource.copy_from(original_filename, dest_filename)

        google_resource.list_blobs_object_path()


if __name__ == '__main__':
    sys.exit(main())
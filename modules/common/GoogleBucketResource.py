import os
from google.cloud import storage, exceptions
import google.auth
import logging
from datetime import datetime
from modules.common import extract_date_from_file

logger = logging.getLogger(__name__)


class GoogleBucketResource(object):

    # args -- tuple of anonymous arguments | kwargs -- dictionary of named arguments
    def __init__(self, *args, **kwargs):
        self.bucket_name = kwargs.get('bucket_name')[0] if kwargs.get('bucket_name')[0] != "" else None
        self.object_path = kwargs.get('bucket_name')[1] if len(kwargs.get('bucket_name')) == 2 else None
        # Issue detect Upload of large files times out. #40
        # storage.blob._DEFAULT_CHUNKSIZE = 5 * 1024 * 1024  # 5 MB
        # storage.blob._MAX_MULTIPART_SIZE = 5 * 1024 * 1024  # 5 MB
        self.client = storage.Client()

    def __del__(self):
        logger.debug('Destroyed instance of %s', __name__)


    @staticmethod
    def has_valid_auth_key(google_credential_key=None):
        if google_credential_key is None:
            logger.info("gsutil will use the default credetial for the user.")
        else:
           os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_credential_key
        try:
            credentials, project = google.auth.default()
            logger.info('\n\tGoogle Bucket connection: %s', project)
        except Exception as error:
            logger.error('Google Auth Error: %s', error)
            raise ValueError("Google credential is not valid!")
        return True

    @staticmethod
    def get_bucket_and_path(google_bucket_param):
        params = list()
        if google_bucket_param is None:
            params.append('')
        else:
            params = google_bucket_param.split('/', 1)
        return params

    def get_full_path(self):
        # the bucket_name is present.
        if self.object_path is None:
            return self.bucket_name
        else:
            return self.bucket_name + '/' + self.object_path

    def get_bucket_name(self):
        return self.bucket_name

    def get_object_path(self):
        return self.object_path

    # Retrieve the list of buckets available for the user
    def get_list_buckets(self):
        return self.client.list_buckets()

    # Retrieve the list of buckets available for the user
    def get_bucket(self):
        if self.bucket_name is None:
            logger.error("Cannot determine path without bucket name.")
            return None

        try:
            bucket = self.client.get_bucket(self.bucket_name)
        except google.cloud.exceptions.NotFound:
            logger.error("Sorry, that bucket {} does not exist!".format(self.bucket_name))
            return None
        except exceptions.Forbidden:
            logger.error(" ERROR: GCS forbidden access, path={}".format(self.bucket_name))
            return None
        return bucket

    # google_resource.list_blobs('es5-sufentanil/tmp/','/', None, None)
    def list_blobs(self, prefix, delimiter, include, exclude):
        list_blobs_dict = {}
        bucket = self.client.get_bucket(self.bucket_name)
        blobs = bucket.list_blobs(prefix=prefix, delimiter=delimiter)

        for blob in blobs:
            logger.debug("Filename: %s , Created: %s, Updated: %s", blob.name, blob.time_created, blob.updated)
            list_blobs_dict[blob.name] = {'created': blob.time_created, 'updated': blob.updated}
            if (exclude is not None) and (exclude in blob.name):
                list_blobs_dict.pop(blob.name, None)
            if (include is not None) and (include not in blob.name):
                list_blobs_dict.pop(blob.name, None)
        return list_blobs_dict

    def list_blobs_object_path(self):
        return self.list_blobs(self.object_path, '', None, None)

    def list_blobs_object_path_excludes(self, excludes_pattern):
        return self.list_blobs(self.object_path, '', None, excludes_pattern)

    def list_blobs_object_path_includes(self, included_pattern):
        return self.list_blobs(self.object_path, '', included_pattern, None)

    def copy_from(self, original_filename, dest_filename, gs_specific_output_dir=None):
        bucket_link = self.get_bucket()
        if bucket_link is None:
            raise ValueError('Invalid google storage bucket {bucket}'.format(bucket=self.bucket_name))

        object_path = self.object_path
        if gs_specific_output_dir is not None:
            object_path = object_path + '/' + gs_specific_output_dir

        blob = bucket_link.blob(object_path + '/' + dest_filename)
        logger.info('Copy the file %s to the bucket %s', original_filename, bucket_link)
        if ".gz" in original_filename:
            blob.content_type = "application/x-gzip"
        else:
            blob.content_type = "text/plain"

        blob.upload_from_filename(filename=original_filename)
        return blob.name

    def is_a_spark_directory(self, filename):
        if (filename.find("/_SUCCESS") > 0) or (filename.find("/part-0") > 0) or (filename.find("/.part-0") > 0) or (
                filename.find("/._") > 0):
            return True
        else:
            return False

    # Return the filename with the latest date. Manage collision of dates only for the latest date.
    def extract_latest_file(self, list_blobs):

        last_recent_file = None
        possible_recent_date_collision = False
        recent_date = datetime.strptime('01-01-1900', '%d-%m-%Y')
        for filename in list_blobs:
            date_file = extract_date_from_file(filename)
            if date_file:
                if date_file == recent_date:
                    if not self.is_a_spark_directory(filename):
                        possible_recent_date_collision = True
                    else:
                        # it is spark dir. Check if it is the same dir
                        if os.path.dirname(filename) != os.path.dirname(last_recent_file):
                            logger.info(filename + " vs " + last_recent_file)
                            possible_recent_date_collision = True
                if date_file > recent_date:
                    possible_recent_date_collision = False
                    recent_date = date_file
                    last_recent_file = filename

        if possible_recent_date_collision:
            # Raise an error. No filename is unique in the recent date selected.
            logger.error("Error TWO files with the same date: %s %s", last_recent_file,
                         recent_date.strftime('%d-%m-%Y'))
            exit(1)

        logger.info("Latest file: %s %s", last_recent_file, recent_date.strftime('%d-%m-%Y'))
        return {"latest_filename": last_recent_file,
                "suffix": recent_date.strftime('%Y-%m-%d'), "spark": self.is_a_spark_directory(last_recent_file)}

    def get_latest_file(self, resource_info):
        if 'excludes' in resource_info:
            list_blobs = self.list_blobs_object_path_excludes(resource_info.excludes)
        elif 'includes' in resource_info:
            list_blobs = self.list_blobs_object_path_includes(resource_info.includes)
        else:
            list_blobs = self.list_blobs_object_path()
        latest_filename_info = self.extract_latest_file(list_blobs)
        return latest_filename_info

    def download_dir(self, dir_to_download, local_dir):
        list_files = []
        dir_name = dir_to_download.rsplit("/", 1)[0]
        bucket = self.get_bucket()
        blobs = bucket.list_blobs(prefix=dir_name)  # Get list of files
        for blob in blobs:
            haed, tail = os.path.split(blob.name)
            filename_destination = local_dir + '/' + tail
            blob.download_to_filename(filename_destination)
            list_files.append(filename_destination)

        return list_files

    def download_file(self, filename_to_download, filename_destination):
        bucket = self.get_bucket()
        blob = bucket.blob(filename_to_download)
        blob.download_to_filename(filename_destination)
        return filename_destination

    def download(self, info):
        if info["is_dir"]:
            self.download_dir(info["file"],info["output"])
        else:
            self.download_file(info["file"],info["output"])

    def blob_metadata(self, blob_name):
        """Prints out a blob's metadata."""
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(self.bucket_name)
        blob = bucket.get_blob(blob_name)

        print(('Blob: {}'.format(blob.name)))
        print(('Bucket: {}'.format(blob.bucket.name)))
        print(('Storage class: {}'.format(blob.storage_class)))
        print(('ID: {}'.format(blob.id)))
        print(('Size: {} bytes'.format(blob.size)))
        print(('Updated: {}'.format(blob.updated)))
        print(('Generation: {}'.format(blob.generation)))
        print(('Metageneration: {}'.format(blob.metageneration)))
        print(('Etag: {}'.format(blob.etag)))
        print(('Owner: {}'.format(blob.owner)))
        print(('Component count: {}'.format(blob.component_count)))
        print(('Crc32c: {}'.format(blob.crc32c)))
        print(('md5_hash: {}'.format(blob.md5_hash)))
        print(('Cache-control: {}'.format(blob.cache_control)))
        print(('Content-type: {}'.format(blob.content_type)))
        print(('Content-disposition: {}'.format(blob.content_disposition)))
        print(('Content-encoding: {}'.format(blob.content_encoding)))
        print(('Content-language: {}'.format(blob.content_language)))
        print(('Metadata: {}'.format(blob.metadata)))

        if blob.retention_expiration_time:
            print(("retentionExpirationTime: {}"
                   .format(blob.retention_expiration_time)))

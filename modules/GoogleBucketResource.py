import os
from google.cloud import storage, exceptions
import google.auth
import logging

logger = logging.getLogger(__name__)

class GoogleBucketResource(object):

    # args -- tuple of anonymous arguments | kwargs -- dictionary of named arguments
    def __init__(self, *args, **kwargs):
        self.bucket_name = kwargs.get('bucket_name')[0] if kwargs.get('bucket_name')[0] != "" else None
        self.object_path = kwargs.get('bucket_name')[1] if len(kwargs.get('bucket_name')) == 2 else None
        self.client = storage.Client()

    def __del__(self):
        logger.debug('Destroyed instance of %s',__name__)

    @staticmethod
    def has_valid_auth_key(google_credential_key):
        if google_credential_key is None:
            return False

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_credential_key
        try:
            credentials, project = google.auth.default()
            logger.info('\n\tGoogle Bucket connection: %s',project)
        except Exception as error:
            logger.error('Google Auth Error: %s',error)
            return False
        return True

    @staticmethod
    def has_google_parameters(google_credential_key, bucket_name):
        if (google_credential_key) is None and (bucket_name is None):
            return False
        if (google_credential_key is not None) and (bucket_name is not None):
            return True
        raise ValueError("--gkey and --google_bucket are mandatory for the google storage access")


    @staticmethod
    def get_bucket_and_path(google_bucket_param):
        params = list()
        if google_bucket_param is None:
            params.append('')
        else:
            params=google_bucket_param.split('/',1)
        return params

    def get_full_path(self):
        # the bucket_name is present.
        if self.object_path is None:
            return self.bucket_name
        else:
            return self.bucket_name+'/'+self.object_path

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
        except exceptions.Forbidden as ef:
            logger.error(" ERROR: GCS forbidden access, path={}".format(self.bucket_name))
            return None
        return bucket



    #google_resource.list_blobs('es5-sufentanil/tmp/','/', None, None)
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

    def copy_from(self, original_filename, dest_filename):
        bucket_link = self.get_bucket()
        if bucket_link is None:
            raise ValueError('Invalid google storage bucket {bucket}'.format(bucket=self.bucket_name))

        blob = bucket_link.blob(self.object_path + '/' + dest_filename)
        logger.info('Copy the file %s to the bucket %s', original_filename, bucket_link)
        blob.upload_from_filename(filename=original_filename)


    def blob_metadata(bucket_name, blob_name):
        """Prints out a blob's metadata."""
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.get_blob(blob_name)

        print('Blob: {}'.format(blob.name))
        print('Bucket: {}'.format(blob.bucket.name))
        print('Storage class: {}'.format(blob.storage_class))
        print('ID: {}'.format(blob.id))
        print('Size: {} bytes'.format(blob.size))
        print('Updated: {}'.format(blob.updated))
        print('Generation: {}'.format(blob.generation))
        print('Metageneration: {}'.format(blob.metageneration))
        print('Etag: {}'.format(blob.etag))
        print('Owner: {}'.format(blob.owner))
        print('Component count: {}'.format(blob.component_count))
        print('Crc32c: {}'.format(blob.crc32c))
        print('md5_hash: {}'.format(blob.md5_hash))
        print('Cache-control: {}'.format(blob.cache_control))
        print('Content-type: {}'.format(blob.content_type))
        print('Content-disposition: {}'.format(blob.content_disposition))
        print('Content-encoding: {}'.format(blob.content_encoding))
        print('Content-language: {}'.format(blob.content_language))
        print('Metadata: {}'.format(blob.metadata))

        if blob.retention_expiration_time:
            print("retentionExpirationTime: {}"
              .format(blob.retention_expiration_time))

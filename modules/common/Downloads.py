import os
import datetime
import logging
from modules.common.Utils import Utils
from modules.common import create_output_dir
from modules.common.DownloadResource import DownloadResource
from modules.common.GoogleBucketResource import GoogleBucketResource

logger = logging.getLogger(__name__)


class Downloads(object):
    """
    Helper for downloading files from HTTPS, HTTP, FTP and GS
    """

    def __init__(self, output_dir):
        """
        Constructor

        :param output_dir: path to download destination folder
        """
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.path_root = output_dir

    def prepare_gs_download(self, gs_info, resource):
        """
        Prepare Google Storage download.

        :param gs_info: Google Storage information object
        :param resource: Download Resource information
        :return: destination information for this download
        """
        if gs_info["spark"]:
            output = os.path.join(self.path_root, resource.path,
                                  resource.output_spark_dir.replace('{suffix}', gs_info["suffix"]))
            create_output_dir(output)
        else:
            create_output_dir(os.path.join(self.path_root, resource.path))
            output = os.path.join(self.path_root, resource.path,
                                  resource.output_filename.replace('{suffix}', gs_info["suffix"]))

        return {'output': output, 'is_dir': gs_info["spark"], 'file': gs_info["latest_filename"]}

    @staticmethod
    def get_latest(google_resource, resource):
        """
        Get the latest file name in a given Google Storage Bucket, specified by a given resource

        :param google_resource: Google Storage Bucket
        :param resource: resource information to look for in the Google Storage Bucket
        :return: the latest filename in the given Google Storage Bucket for the given resource information
        """
        latest_filename = None
        if google_resource.get_bucket() is not None:
            latest_filename = google_resource.get_latest_file(resource)
            if latest_filename["latest_filename"] is None:
                logger.info(f"ERROR: The path={google_resource.get_bucket_name()} does not contain any recent file")
        return latest_filename

    def exec(self, resources_info):
        """
        Download the resources according to their provided information

        :param resources_info: information on the resources to download
        """
        for resource in resources_info.ftp_downloads:
            try:
                path = create_output_dir(os.path.join(self.path_root, resource.path))
                download = DownloadResource(path)
                download.ftp_download(resource)
            except:
                logger.error(f"ERROR: The resource={resource.uri} was not download")

        for resource in resources_info.http_downloads:
            try:
                self.single_http_download(resource)
            except:
                logger.error(f"ERROR: The resource={resource.uri} was not download")

        for resource in resources_info.gs_downloads_latest:
            try:
                param = GoogleBucketResource.get_bucket_and_path(resource.bucket)
                google_resource = GoogleBucketResource(bucket_name=param)
                latest_resource = self.get_latest(google_resource, resource)
                download_info = self.prepare_gs_download(latest_resource, resource)
                google_resource.download(download_info)
            except:
                logger.error(f"ERROR: The resource={resource.bucket} was not download")

    def single_http_download(self, resource):
        download = DownloadResource(create_output_dir(self.path_root + '/' + resource.path))
        return download.execute_download(resource)

    @staticmethod
    def dowload_staging_http(staging_dir, resource):
        download = DownloadResource(staging_dir)
        stage_resource = Utils.resource_for_stage(resource)
        return download.execute_download(stage_resource)

    @staticmethod
    def dowload_staging_ftp(staging_dir, resource):
        download = DownloadResource(staging_dir)
        stage_resource = Utils.resource_for_stage(resource)
        return download.ftp_download(stage_resource)

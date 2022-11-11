import os
import datetime
import logging

from typing import List

from modules.common.Utils import Utils
from modules.common import create_folder
from manifest import ManifestResource, ManifestStatus, get_manifest_service
from modules.common.DownloadResource import DownloadResource
from modules.common.GoogleBucketResource import GoogleBucketResource

logger = logging.getLogger(__name__)


# NOTE I would probably refactor the name of this class, it is in module 'Downloads'
# I would probably call it 'DownloadHelper'
class Downloads(object):
    """
    Helper for downloading files from HTTPS, HTTP, FTP and GS
    """

    def __init__(self, output_dir):
        """
        Constructor.

        :param output_dir: path to download destination folder
        """
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.path_root = output_dir
        self.downloaded_resources = list()

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
            create_folder(output)
        else:
            create_folder(os.path.join(self.path_root, resource.path))
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
                logger.warning(f"The path={google_resource.bucket_name} does not contain any recent file")
        return latest_filename

    def exec(self, resources_info) -> List[ManifestResource]:
        """
        Download the resources according to their provided information.

        :param resources_info: information on the resources to download
        """
        # TODO Those places where the download was not possible, need to report back to the caller.
        downloaded_resources = list()
        for resource in resources_info.ftp_downloads:
            try:
                path = create_folder(os.path.join(self.path_root, resource.path))
                download = DownloadResource(path)
                downloaded_resources.append(download.ftp_download(resource))
            except Exception as e:
                # TODO - Check that we should never find ourselves in this 'except', otherwise it escapes reporting
                logger.error(f"COULD NOT DOWNLOAD resource '{resource.uri}', due to '{e}'")

        for resource in resources_info.http_downloads:
            try:
                downloaded_resources.append(self.single_http_download(resource))
            except Exception as e:
                # TODO - Check that we should never find ourselves in this 'except', otherwise it escapes reporting
                logger.error(f"COULD NOT DOWNLOAD resource '{resource.uri}', due to '{e}'")

        for resource in resources_info.gs_downloads_latest:
            try:
                bucket_name, path = GoogleBucketResource.get_bucket_and_path(resource.bucket)
                google_resource = GoogleBucketResource(bucket_name, path)
                latest_resource = self.get_latest(google_resource, resource)
                download_info = self.prepare_gs_download(latest_resource, resource)
                downloaded_resources.append(google_resource.download(download_info))
            except Exception as e:
                logger.error(f"COULD NOT DOWNLOAD resource '{resource.bucket}', due to '{e}'")
        return downloaded_resources

    def single_http_download(self, resource) -> ManifestResource:
        """
        Perform a single HTTP download

        :param resource: information on the resource to be downloaded
        """
        download = DownloadResource(create_folder(os.path.join(self.path_root, resource.path)))
        return download.execute_download(resource)

    @staticmethod
    def download_staging_http(staging_dir, resource):
        download = DownloadResource(staging_dir)
        stage_resource = Utils.resource_for_stage(resource)
        return download.execute_download(stage_resource)

    @staticmethod
    def download_staging_ftp(staging_dir, resource):
        download = DownloadResource(staging_dir)
        stage_resource = Utils.resource_for_stage(resource)
        return download.ftp_download(stage_resource)

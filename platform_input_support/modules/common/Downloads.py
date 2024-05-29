import os
import datetime
import logging

from typing import List

from platform_input_support.modules.common.Utils import Utils
from platform_input_support.modules.common import create_folder
from platform_input_support.manifest import ManifestResource, ManifestStatus, get_manifest_service
from platform_input_support.modules.common.DownloadResource import DownloadResource
from platform_input_support.modules.common.GoogleBucketResource import GoogleBucketResource

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
        downloaded_resources = list()
        for resource in resources_info.ftp_downloads:
            download_manifest = get_manifest_service().new_resource()
            download_manifest.source_url = resource.uri
            try:
                path = create_folder(os.path.join(self.path_root, resource.path))
                download_manifest = DownloadResource(path).ftp_download(resource)
            except Exception as e:
                download_manifest.msg_completion = f"COULD NOT DOWNLOAD resource '{resource.uri}', due to '{e}'"
                download_manifest.status_completion = ManifestStatus.FAILED
                logger.error(download_manifest.msg_completion)
            finally:
                downloaded_resources.append(download_manifest)

        for resource in resources_info.http_downloads:
            download_manifest = get_manifest_service().new_resource()
            download_manifest.source_url = resource.uri
            try:
                download_manifest = self.single_http_download(resource)
            except Exception as e:
                download_manifest.msg_completion = f"COULD NOT DOWNLOAD resource '{resource.uri}', due to '{e}'"
                download_manifest.status_completion = ManifestStatus.FAILED
                logger.error(download_manifest.msg_completion)
            finally:
                downloaded_resources.append(download_manifest)

        for resource in resources_info.gs_downloads_latest:
            bucket_name, path = GoogleBucketResource.get_bucket_and_path(resource.bucket)
            google_resource = GoogleBucketResource(bucket_name, path)
            try:
                latest_resource = self.get_latest(google_resource, resource)
                download_info = self.prepare_gs_download(latest_resource, resource)
                downloaded_resources.extend(google_resource.download(download_info))
            except Exception as e:
                download_manifest = get_manifest_service().new_resource()
                download_manifest.source_url = resource.bucket
                download_manifest.msg_completion = f"COULD NOT DOWNLOAD resource '{resource.bucket}', due to '{e}'"
                download_manifest.status_completion = ManifestStatus.FAILED
                logger.error(download_manifest.msg_completion)
        return downloaded_resources

    def single_http_download(self, resource) -> ManifestResource:
        """
        Perform a single HTTP download

        :param resource: information on the resource to be downloaded
        """
        download = DownloadResource(create_folder(os.path.join(self.path_root, resource.path)))
        return download.execute_download(resource)

    @staticmethod
    def download_staging_http(staging_dir, resource) -> ManifestResource:
        download = DownloadResource(staging_dir)
        stage_resource = Utils.resource_for_stage(resource)
        return download.execute_download(stage_resource)

    @staticmethod
    def download_staging_ftp(staging_dir, resource) -> ManifestResource:
        download = DownloadResource(staging_dir)
        stage_resource = Utils.resource_for_stage(resource)
        return download.ftp_download(stage_resource)

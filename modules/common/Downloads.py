import datetime
import logging
from modules.common.DownloadResource import DownloadResource
from modules.common import create_output_dir
from definitions import *
from modules.common.GoogleBucketResource import GoogleBucketResource
from modules.common.Utils import Utils

logger = logging.getLogger(__name__)

# Generic class to downloads file from https, http, ftp and GS
class Downloads(object):

    def __init__(self, output_dir):
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')
        self.path_root = output_dir

    def get_gs_path_info(self, gs_info, resource):
        if gs_info["spark"]:
            output = self.path_root + '/' + resource.path  + '/' +  resource.output_spark_dir.replace('{suffix}', gs_info["suffix"])
            create_output_dir(output)
        else:
            create_output_dir(self.path_root + '/' + resource.path)
            output = self.path_root + '/' + resource.path  + '/' +  resource.output_filename.replace('{suffix}', gs_info["suffix"])

        return {'output': output, 'is_dir': gs_info["spark"], 'file': gs_info["latest_filename"]}

    def get_latest(self, google_resource, resource):
        bucket = google_resource.get_bucket()
        latest_filename = None
        if bucket is not None:
            latest_filename = google_resource.get_latest_file(resource)
            if latest_filename["latest_filename"] is None:
                logger.info(f"ERROR: The path={google_resource.get_bucket_name()} does not contain any recent file")
        return latest_filename

    def exec(self, resources_info):
        for resource in resources_info.ftp_downloads:
            try:
                path = create_output_dir(os.path.join(self.path_root, resource.path))
                download = DownloadResource(path)
                filename=download.ftp_download(resource)
            except:
                logger.error(f"ERROR: The resource={resource.uri} was not download")

        for resource in resources_info.http_downloads:
            try:
                filename=self.single_http_download(resource)
            except:
                logger.error(f"ERROR: The resource={resource.uri} was not download")

        for resource in resources_info.gs_downloads_latest:
            try:
                param = GoogleBucketResource.get_bucket_and_path(resource.bucket)
                google_resource = GoogleBucketResource(bucket_name=param)
                latest_resource = self.get_latest(google_resource, resource)
                download_info = self.get_gs_path_info(latest_resource, resource)
                filename=google_resource.download(download_info)
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
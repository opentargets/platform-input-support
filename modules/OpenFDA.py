"""
This module gathers all data related to OpenFDA FAERS database, with a focus on Drug Events.

In addition, a collection of blacklisted events is downloaded for later use in the ETL backend pipeline.
"""

import os
import uuid
import json
import zipfile
import logging
import warnings
import multiprocessing as mp

from datetime import datetime
from urllib.parse import urlparse
from definitions import PIS_OUTPUT_OPENFDA
from .DownloadResource import DownloadResource

logger = logging.getLogger(__name__)

# Parallel kernel
def _do_download_openfda_event_file(download_entry):
    download_url = download_entry['file']
    download_description = download_entry['display_name']
    download_src_filename = os.path.basename(urlparse(download_url).path)
    download_dest_filename = "{}.zip".format(uuid.uuid4())
    download_dest_path = os.path.join(PIS_OUTPUT_OPENFDA, download_dest_filename)
    download_resource_key = "openfda-event-{}".format(download_dest_filename)
    logger.info("Download OpenFDA FAERs '{}', from '{}', destination file name '{}'".format(download_description, download_url, download_src_filename))
    download_resource = type('download_resource', (object,), {
        'uri': download_url,
        'unzip_file': True,
        'resource': download_resource_key,
        'output_filename': download_dest_filename,
        'accept': 'application/zip'
    })
    # Download the file
    downloader = DownloadResource(PIS_OUTPUT_OPENFDA)
    downloader.execute_download(download_resource, 7)
    # Expand the ZIP file
    extracted_filelist = dict()
    with zipfile.ZipFile(download_dest_path, 'r') as zipf:
        for event_file in zipf.filelist:
            unzip_filename = event_file.filename
            unzip_dest_filename = "{}.jsonl".format(uuid.uuid4())
            unzip_dest_path = os.path.join(PIS_OUTPUT_OPENFDA, unzip_dest_filename)
            logger.info("Inflating event file '{}', CRC '{}'".format(unzip_filename, event_file.CRC))
            with zipf.open(unzip_filename, 'r') as compressedf:
                with open(unzip_dest_path, 'w') as inflatedf:
                    logger.info("Extracting event file results")
                    event_data = json.load(compressedf)
                    if event_data['results']:
                        for result in event_data['results']:
                            inflatedf.write(json.dumps(result))
                    else:
                        logger.warning("NO EVENT DATA RESULTS for event file '{}', source URL '{}', description '{}'".format(unzip_filename, download_url, download_description))
            unzip_resource_key = "{}-{}".format(download_resource_key, unzip_dest_filename)
            extracted_filelist[unzip_dest_filename] = {
                'resource': unzip_resource_key,
                'gs_output_dir': unzip_dest_path
            }
    logger.warning("Removing processed ZIP file '{}'".format(download_dest_path))
    os.remove(download_dest_path)
    return extracted_filelist

class OpenFDA(object):
    """
    This class implements the strategy for collection of OpenFDA FAERS drug event data and related information
    """

    def __init__(self, config) -> None:
        self.config = config
        self.write_date = datetime.today().strftime('%Y-%m-%d')
        #logger.info("OpenFDA received configuration: '{}'".format(self.config))

    def _download_selected_event_files(self, repo_metadata):
        downloaded_files = dict()
        # Body
        if repo_metadata:
            logger.info("OpenFDA FAERs metadata received")
            # Parallel data gathering
            logger.info("Prepare download pool of {} processes".format(mp.cpu_count()))
            download_pool = mp.Pool(mp.cpu_count())
            pool_results = download_pool.map(_do_download_openfda_event_file, repo_metadata['results']['drug']['event']['partitions'])
            for result in pool_results:
                downloaded_files.update(result)
        return downloaded_files

    def _download_openfda_faers(self, resource):
        logger.info("OpenFDA available files download, URI '{}' --- START ---".format(resource.uri))
        downloaded_files = dict()
        # TODO - body
        logger.info("Download OpenFDA FAERS repository metadata")
        downloader = DownloadResource(PIS_OUTPUT_OPENFDA)
        download = downloader.execute_download(resource, 3)
        if resource.unzip_file:
            logger.error("UNSUPPORTED file format (ZIP) - URI '{}'".format(resource.uri))
        else:
            if download:
                downloaded_files[download] = {
                    'resource': resource.resource,
                    'gs_output_dir': os.path.join(PIS_OUTPUT_OPENFDA, resource.output_filename)
                }
        repo_metadata = {}
        with open(downloaded_files[download]['gs_output_dir'], 'r') as f:
            repo_metadata = json.load(f)
        downloaded_event_files = self._download_selected_event_files(repo_metadata)
        downloaded_files.update(downloaded_event_files)
        return downloaded_files
    
    def _download_blacklist(self, resource):
        logger.info("OpenFDA blacklisted events download, URI '{}' --- START ---".format(resource.uri))
        downloader = DownloadResource(PIS_OUTPUT_OPENFDA)
        download = downloader.execute_download(resource, 3)
        downloaded_files = dict()
        if resource.unzip_file:
            logger.error("UNSUPPORTED file format (ZIP) - URI '{}'".format(resource.uri))
        else:
            if download:
                downloaded_files[download] = {
                    'resource': resource.resource,
                    'gs_output_dir': os.path.join(PIS_OUTPUT_OPENFDA, resource.output_filename)
                }
        return downloaded_files

    # Step main body
    def run(self):
        logger.info("OpenFDA ETL --- START ---")
        downloaded_files = dict()
        for download_entry in self.config.datasources.downloads:
            if "blacklisted" in download_entry.resource:
                downloaded_files.update(self._download_blacklist(download_entry))
            elif "available" in download_entry.resource:
                downloaded_files.update(self._download_openfda_faers(download_entry))
            else:
                logger.warning("UNSUPPORTED OpenFDA download resource '{}', URI '{}'".format(download_entry.resource, download_entry.uri))
        return downloaded_files

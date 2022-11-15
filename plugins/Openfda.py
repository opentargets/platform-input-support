import os
import json
import logging
import itertools
import multiprocessing as mp

from typing import List
from yapsy.IPlugin import IPlugin
from modules.common import create_folder
from modules.common.Downloads import Downloads
from plugins.helpers.OpenfdaHelper import OpenfdaHelper
from manifest import ManifestResource, ManifestStatus, get_manifest_service

logger = logging.getLogger(__name__)

"""
This module gathers all data related to OpenFDA FAERS database, with a focus on Drug Events.

In addition, a collection of blacklisted events is downloaded for later use in the ETL backend pipeline.
"""


class Openfda(IPlugin):
    """
    This class implements the OpenFDA data collection step
    """

    def __init__(self):
        """
        Constructor, prepares logging subsystem
        """
        self._logger = logging.getLogger(__name__)
        self.step_name = "OpenFDA"

    def _download_selected_event_files(self, repo_metadata, output) -> List[ManifestResource]:
        """
        Collect a subset of the available OpenFDA data, described by the given repository metadata, into a specified
        destination folder

        :param repo_metadata: OpenFDA repository metadata
        :param output: output folder for the collected OpenFDA data
        :return it should return information on the downloaded files, but, in fact, that information is empty
        """
        # Body
        if repo_metadata:
            self._logger.debug("OpenFDA FAERs metadata received")
            fda_output = create_folder(os.path.join(output.prod_dir, "fda-inputs"))
            fda = OpenfdaHelper(fda_output, manifest_service=get_manifest_service())
            # Parallel data gathering
            self._logger.debug("Download processes pool -- {}".format(mp.cpu_count()))
            download_pool_nprocesses = mp.cpu_count() * 2
            download_pool_chunksize = int(
                len(repo_metadata['results']['drug']['event']['partitions']) / download_pool_nprocesses
            )
            with mp.Pool() as download_pool:
                try:
                    return list(itertools.chain.from_iterable(download_pool.map(fda.do_download_openfda_event_file,
                                                                                repo_metadata['results']['drug'][
                                                                                    'event']['partitions'],
                                                                                chunksize=download_pool_chunksize)))
                except Exception as e:
                    self._logger.error("Something went wrong: " + str(e))
        return []

    def _download_openfda_faers(self, resource, output) -> List[ManifestResource]:
        """
        Get OpenFDA repository metadata and kick start the OpenFDA data collection process

        :param resource: download descriptor for OpenFDA repository metadata file
        :param output: output folder for the data collection
        :return: information on the downloaded files
        """
        self._logger.info("OpenFDA available files download, URI '{}' --- START ---".format(resource.uri))
        self._logger.info("Download OpenFDA FAERS repository metadata")
        download = Downloads.download_staging_http(output.staging_dir, resource)
        repo_metadata = {}
        with open(download.path_destination, 'r') as f:
            repo_metadata = json.load(f)
        return self._download_selected_event_files(repo_metadata, output)

    def process(self, conf, output, cmd_conf=None):
        """
        OpenFDA data collection step implementation

        :param conf: OpenFDA step configuration object
        :param output: output folder for collected OpenFDA data
        :param cmd_conf: UNUSED
        """
        self._logger.info("[STEP] BEGIN, openfda")
        manifest_step = get_manifest_service().get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        # TODO Check whether we could retrieve the Bill Of Materials for downloading the OpenFDA dataset
        manifest_step.resources.extend(self._download_openfda_faers(conf.etl.downloads, output))
        get_manifest_service().compute_checksums(manifest_step.resources)
        manifest_step.status_completion = ManifestStatus.COMPLETED
        manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, openfda")

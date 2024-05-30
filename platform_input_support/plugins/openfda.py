import concurrent.futures
import itertools
import json
import os

from loguru import logger
from yapsy.IPlugin import IPlugin

from platform_input_support.manifest import ManifestResource, ManifestStatus, get_manifest_service
from platform_input_support.modules.common import create_folder
from platform_input_support.modules.common.downloads import Downloads
from platform_input_support.plugins.helpers.openfda import OpenFDA as OpenFDAHelper

# This module gathers all data related to OpenFDA FAERS database, with a focus on Drug Events.
# In addition, a collection of blacklisted events is downloaded for later use in the ETL backend pipeline.


class Openfda(IPlugin):
    """OpenFDA data collection step."""

    def __init__(self):
        """Openfda class constructor."""
        self.step_name = 'OpenFDA'

    def _download_selected_event_files(self, repo_metadata, output) -> list[ManifestResource]:
        """Collect a subset of the available OpenFDA data.

        :param repo_metadata: OpenFDA repository metadata
        :param output: output folder for the collected OpenFDA data
        :return it should return information on the downloaded files, but, in fact, that information is empty
        """
        # Body
        if repo_metadata:
            logger.debug('OpenFDA FAERs metadata received')
            fda_output = create_folder(os.path.join(output.prod_dir, 'fda-inputs'))
            fda = OpenFDAHelper(fda_output, manifest_service=get_manifest_service())
            drug_event_partitions = repo_metadata['results']['drug']['event']['partitions']
            with concurrent.futures.ProcessPoolExecutor() as executor:
                max_workers = executor._max_workers
                download_pool_chunksize = int(len(drug_event_partitions) / max_workers)
                logger.debug(f'Max number of workers: {max_workers}')
                try:
                    return list(
                        itertools.chain.from_iterable(
                            executor.map(
                                fda.do_download_openfda_event_file,
                                drug_event_partitions,
                                chunksize=download_pool_chunksize,
                            )
                        )
                    )
                except Exception as e:
                    logger.error(f'Something went wrong: {e}')
        return []

    def _download_openfda_faers(self, resource, output) -> list[ManifestResource]:
        """Get OpenFDA repository metadata and kick start the OpenFDA data collection process.

        :param resource: download descriptor for OpenFDA repository metadata file
        :param output: output folder for the data collection
        :return: information on the downloaded files
        """
        logger.info(f'OpenFDA available files download, URI {resource.uri} --- START ---')
        logger.info('Download OpenFDA FAERS repository metadata')
        download = Downloads.download_staging_http(output.staging_dir, resource)
        repo_metadata = {}
        with open(download.path_destination) as f:
            repo_metadata = json.load(f)
        return self._download_selected_event_files(repo_metadata, output)

    def process(self, conf, output, cmd_conf=None):
        """OpenFDA data collection step implementation.

        :param conf: OpenFDA step configuration object
        :param output: output folder for collected OpenFDA data
        :param cmd_conf: UNUSED
        """
        logger.info('[STEP] BEGIN, openfda')
        manifest_step = get_manifest_service().get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        # TODO - Should I halt the step as soon as I face the first problem?
        # Check whether we could retrieve the Bill Of Materials for downloading the OpenFDA dataset
        manifest_step.status_completion = ManifestStatus.FAILED
        if get_manifest_service().are_all_resources_complete(manifest_step.resources):
            try:
                manifest_step.resources.extend(self._download_openfda_faers(conf.etl.downloads, output))
            except Exception as e:
                manifest_step.msg_completion = f"OpenFDA FAERS events could not be retrieved due to '{e}'"
            else:
                if get_manifest_service().are_all_resources_complete(manifest_step.resources):
                    manifest_step.status_completion = ManifestStatus.COMPLETED
                else:
                    manifest_step.msg_completion = 'COULD NOT retrieve all OpenFDA FAERS events of interest'
        else:
            manifest_step.msg_completion = 'COULD NOT retrieve the OpenFDA FAERS dataset metadata for event selection'
        get_manifest_service().compute_checksums(manifest_step.resources)
        if manifest_step.status_completion == ManifestStatus.COMPLETED:
            manifest_step.msg_completion = 'The step has completed its data collection'
        else:
            logger.error(manifest_step.msg_completion)
        # TODO - Validation
        logger.info('[STEP] END, openfda')

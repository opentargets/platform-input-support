import os
import logging

from typing import List
from yapsy.IPlugin import IPlugin
from modules.common import create_folder
from modules.common.Downloads import Downloads
from modules.common.ElasticsearchHelper import ElasticsearchInstance
from manifest import ManifestResource, ManifestStatus, get_manifest_service

logger = logging.getLogger(__name__)


class Drug(IPlugin):
    """
    Drug data collection step implementation
    """

    def __init__(self):
        """
        Constructor, prepare logging subsystem and time stamp
        """
        self._logger = logging.getLogger(__name__)
        self.step_name = "Drug"

    def _download_elasticsearch_data(self, output_dir, url, indices) -> List[ManifestResource]:
        """
        Query elasticsearchReader for each index specified in indices and saves results as jsonl files at output_dir.

        :param output_dir: output folder
        :param url: Elastic Search URL
        :param indices: indices for querying Elastic Search
        :return: list of files successfully saved.
        """
        download_manifests = []
        elasticsearch_reader = ElasticsearchInstance(url)
        # TODO Easy point of improvement, parallelize indexes data collection by using one process per index
        for index in list(indices.values()):
            index_name = index['name']
            outfile = os.path.join(output_dir, "{}.jsonl".format(index_name))
            logger.info("Downloading Elasticsearch data from index {}, to file '{}'".format(index_name, outfile))
            index_manifest = get_manifest_service().new_resource()
            index_manifest.source_url = f"{url}/{index_name}"
            index_manifest.path_destination = outfile
            if not elasticsearch_reader.is_reachable():
                index_manifest.status_completion = ManifestStatus.FAILED
                index_manifest.msg_completion = \
                    f"FAILED to retrieve index '{index_name}', UNREACHABLE Elastic Search Service at '{url}'"
                logger.error(index_manifest.msg_completion)
            else:
                docs_saved = 0
                try:
                    docs_saved = elasticsearch_reader.get_fields_on_index(index_name, outfile, index['fields'])
                except Exception as e:
                    index_manifest.status_completion = ManifestStatus.FAILED
                    index_manifest.msg_completion = f"FAILED to retrieve index '{index_name}' due to '{e}'"
                    logger.error(index_manifest.msg_completion)
                else:
                    if docs_saved > 0:
                        logger.info("Successfully downloaded {} documents from index {}"
                                    .format(docs_saved, index_name)
                                    )
                    else:
                        logger.warning("EMPTY INDEX with name {}.".format(index_name))
                    # There could be an empty index, which means its corresponding file is empty,
                    # or maybe non-existent
                    index_manifest.status_completion = ManifestStatus.COMPLETED
                    index_manifest.msg_completion = f"Selected fields: {','.join(index['fields'])}," \
                                                    f" #{docs_saved} documents"
            download_manifests.append(index_manifest)
        return download_manifests

    # TODO We should refactor this out into a generic Elastic Search Helper
    def _handle_elasticsearch(self, source, output_dir) -> List[ManifestResource]:
        """
        Helper function to handle datasources which use Elasticsearch and returns list of files downloaded.

        :param source: `datasource` entry from the `config.yaml` file.
        :param output_dir: output folder
        :return: list of files downloaded.
        """

        if source.url is not None and isinstance(source.url, str):
            logger.info("{} indices found for {}.".format(len(source.indices), source))
            return self._download_elasticsearch_data(output_dir, source.url, source.indices)
        logger.error("Unable to validate host and port for Elasticsearch connection.")
        return []

    def download_indices(self, conf, output) -> List[ManifestResource]:
        """
        Download the specified indices from Elastic Search into the given output folder

        :param conf: configuration object
        :param output: output folder information
        :return: downloaded files listing
        """
        return self._handle_elasticsearch(
            conf.etl.chembl,
            create_folder(os.path.join(output.prod_dir, conf.etl.chembl.path))
        )

    def process(self, conf, output, cmd_conf=None):
        """
        Drug pipeline step implementation

        :param conf: step configuration object
        :param output: output folder
        :param cmd_conf: UNUSED
        """
        # TODO - Handle errors in the process and report back
        self._logger.info("[STEP] BEGIN, Drug")
        manifest_step = get_manifest_service().get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        # TODO - Should I halt the step as soon as I face the first problem?
        manifest_step.resources.extend(self.download_indices(conf, output))
        # We try to compute checksums for whatever was collected
        get_manifest_service().compute_checksums(manifest_step.resources)
        if not get_manifest_service().are_all_resources_complete(manifest_step.resources):
            manifest_step.status_completion = ManifestStatus.FAILED
            manifest_step.msg_completion = "COULD NOT retrieve all the resources"
        # TODO - Validation
        if manifest_step.status_completion != ManifestStatus.FAILED:
            manifest_step.status_completion = ManifestStatus.COMPLETED
            manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, Drug")

import os

from loguru import logger
from yapsy.IPlugin import IPlugin

from platform_input_support.manifest import ManifestResource, ManifestStatus, get_manifest_service
from platform_input_support.modules.common import create_folder
from platform_input_support.modules.common.downloads import Downloads
from platform_input_support.modules.common.elasticsearch_helper import ElasticsearchInstance


class Drug(IPlugin):
    """Drug data collection step."""

    def __init__(self):
        """Drug class constructor."""
        self.step_name = 'Drug'

    def _download_elasticsearch_data(self, output_dir, url, indices) -> list[ManifestResource]:
        """Query elasticsearchReader for each index specified in indices and saves results as jsonl files at output_dir.

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
            outfile = os.path.join(output_dir, f'{index_name}.jsonl')
            logger.info(f'Downloading Elasticsearch data from index {index_name} to file {outfile}')
            index_manifest = get_manifest_service().new_resource()
            index_manifest.source_url = f'{url}/{index_name}'
            index_manifest.path_destination = outfile
            if not elasticsearch_reader.is_reachable():
                index_manifest.status_completion = ManifestStatus.FAILED
                index_manifest.msg_completion = (
                    f"FAILED to retrieve index '{index_name}', UNREACHABLE Elastic Search Service at '{url}'"
                )
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
                        logger.info(f'Successfully downloaded {docs_saved} documents from index {index_name}')
                    else:
                        logger.warning(f'EMPTY INDEX with name {index_name}')
                    # There could be an empty index, which means its corresponding file is empty,
                    # or maybe non-existent
                    index_manifest.status_completion = ManifestStatus.COMPLETED
                    fields = ','.join(index['fields'])
                    index_manifest.msg_completion = f'Selected fields: {fields}, #{docs_saved} documents'
            download_manifests.append(index_manifest)
        return download_manifests

    # TODO We should refactor this out into a generic Elastic Search Helper
    def _handle_elasticsearch(self, source, output_dir) -> list[ManifestResource]:
        """Handle datasources which use Elasticsearch and returns list of files downloaded.

        :param source: `datasource` entry from the `config.yaml` file.
        :param output_dir: output folder
        :return: list of files downloaded.
        """
        if source.url is not None and isinstance(source.url, str):
            logger.info(f'{len(source.indices)} indices found for {source}')
            return self._download_elasticsearch_data(output_dir, source.url, source.indices)
        logger.error('Unable to validate host and port for Elasticsearch connection.')
        return []

    def download_indices(self, conf, output) -> list[ManifestResource]:
        """Download the specified indices from Elastic Search into the given output folder.

        :param conf: configuration object
        :param output: output folder information
        :return: downloaded files listing
        """
        return self._handle_elasticsearch(
            conf.etl.chembl, create_folder(os.path.join(output.prod_dir, conf.etl.chembl.path))
        )

    def process(self, conf, output, cmd_conf=None):
        """Drug pipeline step implementation.

        :param conf: step configuration object
        :param output: output folder
        :param cmd_conf: UNUSED
        """
        # TODO - Handle errors in the process and report back
        logger.info('[STEP] BEGIN, Drug')
        manifest_step = get_manifest_service().get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        # TODO - Should I halt the step as soon as I face the first problem?
        manifest_step.resources.extend(self.download_indices(conf, output))
        # We try to compute checksums for whatever was collected
        get_manifest_service().compute_checksums(manifest_step.resources)
        if not get_manifest_service().are_all_resources_complete(manifest_step.resources):
            manifest_step.status_completion = ManifestStatus.FAILED
            manifest_step.msg_completion = 'COULD NOT retrieve all the resources'
        # TODO - Validation
        if manifest_step.status_completion != ManifestStatus.FAILED:
            manifest_step.status_completion = ManifestStatus.COMPLETED
            manifest_step.msg_completion = 'The step has completed its execution'
        logger.info('[STEP] END, Drug')

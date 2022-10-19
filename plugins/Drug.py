import os
import logging
import warnings
from datetime import datetime
from yapsy.IPlugin import IPlugin
from modules.common import create_folder
from modules.common.Downloads import Downloads
from modules.common.ElasticsearchHelper import ElasticsearchInstance

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

    def _download_elasticsearch_data(self, output_dir, url, indices):
        """
        Query elasticsearchReader for each index specified in indices and saves results as jsonl files at output_dir.

        :param output_dir: output folder
        :param url: Elastic Search URL
        :param indices: indices for querying Elastic Search
        :return: list of files successfully saved.
        """
        results = []
        elasticsearch_reader = ElasticsearchInstance(url)
        if elasticsearch_reader.is_reachable():
            for index in list(indices.values()):
                index_name = index['name']
                outfile = os.path.join(output_dir, "{}.jsonl".format(index_name))

                logger.info("Downloading Elasticsearch data from index {}, to file '{}'".format(index_name, outfile))
                docs_saved = elasticsearch_reader.get_fields_on_index(index_name, outfile, index['fields'])
                # docs = elasticsearch_reader.get_fields_on_index(index_name, index['fields'])
                # elasticsearch_reader.write_elasticsearch_docs_as_jsonl(docs, outfile)
                if docs_saved > 0:
                    logger.info("Successfully downloaded {} documents from index {}".format(docs_saved, index_name))
                else:
                    logger.warning("Failed to download all records from {}.".format(index_name))
                results.append(outfile)
        else:
            logger.error("Unable to reach ChEMBL Elasticsearch! "
                         "at URL '{}', Cannot collect necessary data.".format(url))
            warnings.warn("ChEMBL Elasticsearch is unreachable: "
                          "URL '{}', check network settings.".format(url))
        return results

    # TODO We should refactor this out into a generic Elastic Search Helper
    def _handle_elasticsearch(self, source, output_dir):
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

    def download_indices(self, conf, output):
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
        Downloads(output.prod_dir).exec(conf)
        self.download_indices(conf, output)
        self._logger.info("[STEP] END, Drug")

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
        self.write_date = datetime.today().strftime('%Y-%m-%d')

    def _download_elasticsearch_data(self, output_dir, url, port, indices):
        """
        Query elasticsearchReader for each index specified in indices and saves results as jsonl files at output_dir.

        :param output_dir: output folder
        :param url: Elastic Search URL
        :param port: Elastic Search port
        :param indices: indices for querying Elastic Search
        :return: list of files successfully saved.
        """
        results = []
        elasticsearch_reader = ElasticsearchInstance(url, port)
        if elasticsearch_reader.is_reachable():
            for index in list(indices.values()):
                index_name = index['name']
                outfile = os.path.join(output_dir, "{}-{}.jsonl".format(index_name, self.write_date))

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
                         "at URL '{}', port '{}' Cannot collect necessary data.".format(url, port))
            warnings.warn("ChEMBL Elasticsearch is unreachable: "
                          "URL '{}', port '{}', check network settings.".format(url, port))
        return results

    def _handle_elasticsearch(self, source, output_dir):
        """Helper function to handle datasources which use Elasticsearch and returns list of files downloaded.
        :param source: `datasource` entry from the `config.yaml` file.
        :return: list of files downloaded.
        """

        def _validate_host(host):
            logger.debug("Validating elasticsearch host from config.")
            return host is not None and isinstance(host, str)

        def _validate_port(port):
            logger.debug("Validating elasticsearch port from config.")
            return port is not None and isinstance(port, int)

        indices = source.indices
        output_dir = output_dir
        host = source.url
        port = source.port

        if _validate_host(host) and _validate_port(port):
            logger.info("{} indices found for {}.".format(len(indices), source))
            files = self._download_elasticsearch_data(output_dir, host, port, indices)
            return files
        else:
            logger.error("Unable to validate host and port for Elasticsearch connection.")
            return []

    def download_indices(self, conf, output):
        output_dir = create_folder(output.prod_dir + "/" + conf.etl.chembl.path)
        es_files_written = self._handle_elasticsearch(conf.etl.chembl, output_dir)
        return es_files_written

    def process(self, conf, output, cmd_conf=None):
        """
        Drug pipeline step implementation

        :param conf: step configuration object
        :param output: output folder
        :param cmd_conf: UNUSED
        """
        self._logger.info("Drug step")
        Downloads(output.prod_dir).exec(conf)
        self._logger.info("Drug download indices")
        self.download_indices(conf, output)

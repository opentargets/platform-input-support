import logging

from yapsy.IPlugin import IPlugin
from datetime import datetime
from modules.common import create_output_dir
# from modules.common.DownloadResource import DownloadResource
from modules.common.Downloads import Downloads
from modules.common.ElasticsearchReader import ElasticsearchReader
from datetime import datetime
import logging
import warnings
# import os
import zipfile

logger = logging.getLogger(__name__)

"""

"""


class Drug(IPlugin):

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.write_date = datetime.today().strftime('%Y-%m-%d')

    def _download_elasticsearch_data(self, output_dir, url, port, indices):
        """
        Query elasticsearchReader for each index specified in indices and saves results as jsonl files at output_dir.
        :return: list of files successfully saved.
        """
        results = []
        elasticsearch_reader = ElasticsearchReader(url, port)
        if elasticsearch_reader.confirm_es_reachable():
            for index in list(indices.values()):
                index_name = index['name']
                outfile = output_dir + '/' + index_name + "-" + self.write_date + ".jsonl"

                logger.info("Downloading Elasticsearch data from index {}".format(index_name))
                docs_saved = elasticsearch_reader.get_fields_on_index(index_name, outfile, index['fields'])
                # docs = elasticsearch_reader.get_fields_on_index(index_name, index['fields'])
                # elasticsearch_reader.write_elasticsearch_docs_as_jsonl(docs, outfile)
                if docs_saved > 0:
                    logger.info("Successfully downloaded {} documents from index {}".format(docs_saved, index_name))
                else:
                    logger.warning("Failed to download all records from {}.".format(index_name))
                results.append(outfile)
        else:
            logger.error("Unable to reach ChEMBL Elasticsearch! Cannot collect necessary data.")
            warnings.warn("ChEMBL Elasticsearch is unreachable: check network settings.")
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
        output_dir = create_output_dir(output.prod_dir+"/" + conf.etl.chembl.path)
        es_files_written = self._handle_elasticsearch(conf.etl.chembl, output_dir)
        return es_files_written

    def process(self, conf, output, cmd_conf):
        """
        Download all resources specified in `config.yaml` and return dictionary of files downloaded.

        The returned dictionary has form k -> {'resource': <filename>, 'gs_output_dir': <output as in config>} so that
        it matches the structure of other steps and can be uploaded to GCP.
        """
        self._logger.info("Drug step")
        Downloads(output.prod_dir).exec(conf)
        self._logger.info("Drug download indices")
        self.download_indices(conf, output)

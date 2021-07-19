import os
import zipfile

from definitions import PIS_OUTPUT_CHEMBL_ES, PIS_OUTPUT_DRUG
from .DownloadResource import DownloadResource
from .common import ElasticsearchReader
from .common.ElasticsearchReader import ElasticsearchReader
from datetime import datetime
import logging
import warnings

logger = logging.getLogger(__name__)


class Drug(object):
    """
    Drug is a step in Platform Input Support to facilitate the retrieval of resources specified in the `config.yaml` file's
    `drug` key.
    """

    def __init__(self, config_dict):
        """
        :param config_dict: 'drug' key in the reference config file.
        """
        self._logger = logging.getLogger(__name__)
        self.config = config_dict
        self.write_date = datetime.today().strftime('%Y-%m-%d')
        self.sources = config_dict['datasources']

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
                    logger.warn("Failed to download all records from {}.".format(index_name))
                results.append(outfile)
        else:
            logger.error("Unable to reach ChEMBL Elasticsearch! Cannot collect necessary data.")
            warnings.warn("ChEMBL Elasticsearch is unreachable: check network settings.")
        return results

    def _handle_elasticsearch(self, source):
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

        indices = source['indices']
        output_dir = PIS_OUTPUT_CHEMBL_ES
        host = source['url']
        port = source['port']

        if _validate_host(host) and _validate_port(port):
            logger.info("{} indices found for {}.".format(len(indices), source))
            files = self._download_elasticsearch_data(output_dir, host, port, indices)
            return files
        else:
            logger.error("Unable to validate host and port for Elasticsearch connection.")
            return []

    def get_all(self):
        """
        Download all resources specified in `config.yaml` and return dictionary of files downloaded.

        The returned dictionary has form k -> {'resource': <filename>, 'gs_output_dir': <output as in config>} so that
        it matches the structure of other steps and can be uploaded to GCP.
        """
        downloaded_files = {}  # key: source, values: {}
        for sourceKey in list(self.sources.keys()):
            if sourceKey == "chembl":
                es_files_written = self._handle_elasticsearch(self.sources[sourceKey])
                for f in es_files_written:
                    downloaded_files[f] = {'resource': "drug-{}".format(f), 'gs_output_dir': self.config[
                        'gs_output_dir']}
            elif sourceKey == "downloads":
                download = DownloadResource(PIS_OUTPUT_DRUG)
                for entry in self.sources[sourceKey]:
                    if entry.unzip_file:
                        destination_filename = download.execute_download(entry)
                        with zipfile.ZipFile(destination_filename, 'r') as zip_ref:
                            file = zip_ref.filelist[0].filename
                            zip_ref.extract(file, PIS_OUTPUT_DRUG)
                            os.rename(os.path.join(PIS_OUTPUT_DRUG, file), os.path.join(PIS_OUTPUT_DRUG,
                                                                                        entry.output_filename))
                            downloaded_files[destination_filename] = {'resource': entry.resource,
                                                                      'gs_output_dir': os.path.join(PIS_OUTPUT_DRUG,
                                                                                                    entry.output_filename)}
                        logger.info("Files downloaded: %s", destination_filename)
            else:
                logger.warn("Unrecognised drug datasource: %s".format(sourceKey))
        return downloaded_files

import json
import logging
import requests

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, utils
from requests import ConnectionError

logger = logging.getLogger(__name__)


class ElasticsearchReader:
    """
    Wrapper over an Elasticsearch instance.
    """

    def __init__(self, host, port):
        self.PORT = port
        self.HOST = host
        logger.info("Creating ElasticsearchReader with url: {}, port: {}".format(self.HOST, self.PORT))
        self.es = Elasticsearch([{'host': self.HOST, 'port': self.PORT}])

    def confirm_es_reachable(self):
        """Pings configured Elasticsearch instance and returns true if reachable, false otherwise"""
        try:
            request = requests.head("http://{}:{}".format(self.HOST, self.PORT), timeout=1)
            return request.ok
        except ConnectionError as error:
            logger.error("Unable to reach {}. Error msg: ".format(self.HOST, error))
            return False

    def get_fields_on_index(self, index, fields):
        """
        Return all documents from `index` returning only the `fields` specified.
        :param index: Elasticsearch index to query as Str
        :param fields: subset of fields to return as List[Str]
        :return: List of dictionary entries including `fields` if available.
        """

        def _process_hit_value(field_value):
            """
            :param field_value: Value wrapped in an Elasticsearch wrapper
            :return: Json serializable version of v
            """
            if isinstance(field_value, utils.AttrList):
                return field_value._l_
            elif isinstance(field_value, utils.AttrDict):
                return field_value._d_
            else:
                return field_value

        out = []

        s = Search(index=index, using=self.es)
        s = s.source(fields=fields)
        for hit in s.scan():
            hit_dict = {}
            for f in fields:
                if f in hit:
                    hit_dict[f] = _process_hit_value(hit[f])
                else:
                    logger.error("field \"%s\" not found on document from index: %s", f, index)
            out.append(hit_dict)
        return out

    def write_elasticsearch_docs_as_jsonl(self, docs, fname):
        """
        Write list of elasticsearch objects to file as jsonl format.
        :param fname: file to write contents of `doc`.
        :param docs: List of elasticsearch documents represented as dictionaries. Each document will be written as a
        standalone json object (jsonl).
        :return: None
        """
        with open(fname, 'w') as outfile:
            for doc in docs:
                json.dump(doc, outfile)
                outfile.write('\n')
        logger.info("Wrote {} documents to {}.".format(len(docs), fname))

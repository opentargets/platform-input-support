import json
import sys
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Any, Self

import elasticsearch
import elasticsearch.helpers
from elasticsearch import Elasticsearch as Es
from elasticsearch.exceptions import ElasticsearchException
from elasticsearch.helpers import ScanError
from loguru import logger

from platform_input_support.manifest.models import Resource
from platform_input_support.tasks import Task, TaskDefinition, report
from platform_input_support.util.errors import TaskAbortedError
from platform_input_support.util.fs import absolute_path, check_fs
from platform_input_support.util.misc import list_str
from platform_input_support.validators import v
from platform_input_support.validators.elasticsearch import counts

BUFFER_SIZE = 20000


class ElasticsearchError(Exception):
    pass


@dataclass
class ElasticsearchDefinition(TaskDefinition):
    url: str
    destination: Path
    index: str
    fields: list[str]


class Elasticsearch(Task):
    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: ElasticsearchDefinition
        self.es: Es
        self.doc_count: int = 0
        self.doc_written: int = 0

    # destroy es connection to avoid pickling issues with multiprocessing
    def close_es(self):
        if hasattr(self, 'es'):
            self.es.close()
            del self.es

    @report
    def run(self, *, abort: Event) -> Self:
        url = self.definition.url
        index = self.definition.index
        fields = self.definition.fields
        destination = absolute_path(self.definition.destination)
        check_fs(destination)

        logger.debug(f'connecting to elasticsearch at {url}')
        try:
            self.es = Es(url)
        except ElasticsearchException as e:
            self.close_es()
            raise ElasticsearchError(f'connection error: {e}')

        logger.debug(f'scanning index {index} with fields {list_str(fields)}')
        try:
            self.doc_count = self.es.count(index=index)['count']
        except ElasticsearchException as e:
            self.close_es()
            raise ElasticsearchError(f'error getting index count on index {index}: {e}')
        logger.info(f'index {index} has {self.doc_count} documents')

        buffer: list[dict[str, Any]] = []
        try:
            for hit in elasticsearch.helpers.scan(
                client=self.es,
                index=index,
                query={'query': {'match_all': {}}, '_source': fields},
            ):
                buffer.append(hit['_source'])
                if len(buffer) >= BUFFER_SIZE:
                    logger.trace('flushing buffer')
                    self._write_docs(buffer, destination)
                    buffer.clear()

                    if abort and abort.is_set():
                        raise TaskAbortedError
        except ScanError as e:
            logger.warning(f'error scanning index {index}: {e}')
            raise ElasticsearchError(f'error scanning index {index}: {e}')

        self._write_docs(buffer, destination)
        logger.debug(f'wrote {self.doc_written}/{self.doc_count} documents to {destination}')
        self.resource = Resource(source=f'{url}/{index}', destination=str(self.definition.destination))
        self.close_es()
        return self

    def _write_docs(self, docs: list[dict[str, Any]], destination: Path):
        try:
            with open(destination, 'a+') as f:
                for d in docs:
                    json.dump(d, f)
                    f.write('\n')
            self.doc_written += len(docs)

        except OSError as e:
            self.close_es()
            raise ElasticsearchError(f'error writing to {destination}: {e}')

        logger.debug(f'wrote {len(docs)} ({self.doc_written}/{self.doc_count}) documents to {destination}')
        logger.debug(f'the dict was taking up {sys.getsizeof(docs)} bytes of memory')
        docs.clear()

    def validate(self, *, abort: Event) -> Self:
        v(
            counts,
            self.definition.url,
            self.definition.index,
            self.definition.destination,
        )

        return self

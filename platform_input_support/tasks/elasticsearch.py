import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from elastic_transport import ApiError
from elasticsearch import Elasticsearch as Elasticsearch_
from elasticsearch_dsl import Search, utils
from loguru import logger

from platform_input_support.config import config

from . import Task, TaskMapping, report_to_manifest

BUFFER_SIZE = 100000


class ElasticsearchError(Exception):
    pass


@dataclass
class ElasticsearchMapping(TaskMapping):
    url: str
    destination: str
    index: str
    fields: list[str]


class Elasticsearch(Task):
    def __init__(self, config: TaskMapping):
        super().__init__(config)
        self.config: ElasticsearchMapping
        self.es: Elasticsearch_
        self.doc_count: int = 0
        self.doc_written: int = 0

    def _prepare_path(self) -> Path:
        destination = Path(f'{config.output_path}/{self.config.destination}/{self.config.index}.jsonl')

        try:
            logger.info(f'ensuring path {destination.parent} exists and {destination.name} does not')
            destination.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ElasticsearchError(f'error creating path {self.config.destination}: {e}')

        if destination.is_file():
            raise ElasticsearchError(f'file {self.config.destination} already exists')

        return destination

    @report_to_manifest
    def run(self):
        destination = self._prepare_path()

        try:
            logger.debug(f'connecting to {self.config.url}')
            self.es = Elasticsearch_(self.config.url)
        except ConnectionError as e:
            raise ElasticsearchError(f'connection error: {e}')

        index, fields = self.config.index, self.config.fields
        source: Search
        logger.debug(f'scanning index {index} with fields {fields}')

        try:
            self.doc_count = self.es.count(index=index)['count']
        except ApiError as e:
            raise ElasticsearchError(f'error getting index count on index {index}: {e}')
        logger.info(f'index {index} has {self.doc_count} documents')

        try:
            search = Search(using=self.es, index=index)
            source = search.source(fields=list(fields))
        except ApiError as e:
            raise ElasticsearchError(f'scan error on index {index}: {e}')

        doc_buffer: list[dict[str, Any]] = []

        for hit in source.scan():
            doc: dict[str, Any] = {}

            for field in fields:
                f = hit[field]

                if isinstance(f, utils.AttrList):
                    doc[field] = f._l_
                elif isinstance(f, utils.AttrDict):
                    doc[field] = f._d_
                else:
                    doc[field] = f

            doc_buffer.append(doc)
            if len(doc_buffer) >= BUFFER_SIZE:
                logger.trace('emtying buffer')
                self._write_docs(doc_buffer, destination)
                doc_buffer.clear()

        self._write_docs(doc_buffer, destination)
        return f'wrote {self.doc_written}/{self.doc_count} documents to {destination}'

    def _write_docs(self, docs: list[dict[str, Any]], destination: Path):
        try:
            with open(destination, 'a+') as f:
                for d in docs:
                    json.dump(d, f)
                    f.write('\n')
            self.doc_written += len(docs)

        except OSError as e:
            raise ElasticsearchError(f'error writing to {destination}: {e}')

        logger.debug(f'wrote {len(docs)} ({self.doc_written}/{self.doc_count}) documents to {destination}')
        logger.trace(f'the dict was taking up {sys.getsizeof(docs)} bytes of memory')
        docs.clear()

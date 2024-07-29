import subprocess
from pathlib import Path

from elasticsearch import Elasticsearch as Es
from loguru import logger

from platform_input_support.util.fs import get_full_path


# fastest way to count lines is calling wc -l
def _wccount(filename):
    out = subprocess.Popen(
        ['/usr/bin/wc', '-l', filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).communicate()[0]
    return int(out.partition(b' ')[0])


def counts(url: str, index: str, local_path: Path) -> bool:
    logger.debug(f'checking if document count at {url}/{index} and {local_path} match')

    es = Es(url)
    remote_doc_count = es.count(index=index)['count']
    local_doc_count = _wccount(get_full_path(local_path))

    logger.debug(f'checking if {remote_doc_count} == {local_doc_count}')
    return remote_doc_count == local_doc_count

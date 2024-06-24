from typing import Any

from loguru import logger

from platform_input_support.manifest.models import RootManifest, Status, StepManifest
from platform_input_support.util.misc import date_str


def recount(items: list[Any] | dict[str, Any], manifest: StepManifest | RootManifest) -> None:
    total = len(items)
    succeeded = 0
    failed = 0
    aborted = 0

    if isinstance(items, dict):
        item_list = list(items.values())
    else:
        item_list = items

    for i in item_list:
        if i.status == Status.NOT_COMPLETED:
            manifest.status = Status.FAILED
            logger.error(f'{i.__class__} {i.name} was interrupted for an unknown reason')
        if i.status == Status.ABORTED:
            manifest.status = Status.FAILED
            aborted += 1
        elif i.status == Status.FAILED:
            manifest.status = Status.FAILED
            failed += 1
        else:
            succeeded += 1

    succeeded_summary = f'{succeeded}/{total} tasks succeeded'
    failed_summary = f', {failed}/{total} tasks failed' if failed else ''
    aborted_summary = f', {aborted}/{total} tasks aborted' if aborted else ''
    manifest.log.append(f'run {date_str()} summary: {succeeded_summary}{failed_summary}{aborted_summary}')

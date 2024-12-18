"""Manifest utility functions."""

from platform_input_support.config import settings
from platform_input_support.manifest.models import Result, RootManifest, StepManifest
from platform_input_support.util.misc import date_str


def recount(manifest: RootManifest | StepManifest) -> None:
    """Recount the results of the manifest.

    This function will recount the results of the manifest and log the summary.

    :param manifest: The manifest to recount.
    :type manifest: RootManifest | StepManifest
    """
    if isinstance(manifest, RootManifest):
        items = manifest.steps
        item_type = 'steps' if len(items) > 1 else 'step'
    elif isinstance(manifest, StepManifest):
        item_type = 'tasks' if len(manifest.tasks) > 1 else 'task'
        items = manifest.tasks

    counts = {str(r): 0 for r in Result}

    for i in list(items.values()) if isinstance(items, dict) else items:
        counts[str(i.result)] += 1

    manifest.log.append(f'---- [ {date_str()} run summary ]----')
    manifest.log.append(', '.join([f'{k}={v}' for k, v in settings().model_dump().items()]))
    for k, v in counts.items():
        if v > 0:
            manifest.log.append(f'{v} {k} {item_type}')

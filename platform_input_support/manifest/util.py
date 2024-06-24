from platform_input_support.manifest.models import Result, RootManifest, StepManifest
from platform_input_support.util.misc import date_str


def recount(manifest: RootManifest | StepManifest) -> None:
    if isinstance(manifest, RootManifest):
        item_type = 'steps'
        items = manifest.steps
    elif isinstance(manifest, StepManifest):
        item_type = 'tasks'
        items = manifest.tasks

    counts = {str(r): 0 for r in Result}

    for i in list(items.values()) if isinstance(items, dict) else items:
        counts[str(i.result)] += 1

    manifest.log.append(f'---- [ {date_str()} run summary ]----')
    for i in counts:
        manifest.log.append(f'{counts[i]} {i.lower()} {item_type}')

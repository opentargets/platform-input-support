import sys
from datetime import datetime
from typing import TYPE_CHECKING

from loguru import logger
from pydantic import ValidationError
from pydantic_core import PydanticSerializationError

from platform_input_support.config import settings, steps
from platform_input_support.helpers import google_helper
from platform_input_support.manifest.models import RootManifest, StepManifest
from platform_input_support.manifest.util import recount
from platform_input_support.util.errors import PISError
from platform_input_support.util.fs import get_full_path
from platform_input_support.util.misc import date_str

if TYPE_CHECKING:
    from platform_input_support.step import Step

MANIFEST_FILENAME = 'manifest.json'


class Manifest:
    def __init__(self):
        self._manifest = self._fetch_manifest() or self._init_manifest()

    def _init_manifest(self) -> RootManifest:
        new_manifest = RootManifest()
        for step in steps():
            new_manifest.steps[step] = StepManifest(name=step)
        return new_manifest

    def _fetch_manifest(self) -> RootManifest | None:
        manifest_str: str | None = None

        # try fetching manifest from google cloud storage
        if google_helper().is_ready:
            manifest_path = f'{settings().gcs_url}/{MANIFEST_FILENAME}'
            try:
                manifest_str = google_helper().download(manifest_path)
            except PISError:
                logger.warning('manifest file not found in gcs')

        # try fetching manifest from local file system
        if not manifest_str:
            manifest_path = get_full_path(MANIFEST_FILENAME)

            try:
                manifest_str = manifest_path.read_text()
            except FileNotFoundError:
                logger.warning(f'manifest file not found in {manifest_path}')
                return None
            except (OSError, PermissionError, ValueError) as e:
                logger.critical(f'error reading manifest file: {e}')
                sys.exit(1)

        try:
            manifest = RootManifest().model_validate_json(manifest_str)
        except ValidationError as e:
            logger.critical(f'error validating manifest file: {e}')
            sys.exit(1)

        logger.info(f'previous manifest found, last modified {date_str(manifest.modified)}')
        return manifest

    def update(self, step: 'Step'):
        self._manifest.steps[step.name] = step._manifest
        self._manifest.modified = datetime.now()
        self._manifest.result = step._manifest.result

        recount(self._manifest)

    def save(self):
        """Save the manifest to the local file system."""
        manifest_path = get_full_path(MANIFEST_FILENAME)

        try:
            json_str = self._manifest.model_dump_json(indent=2, serialize_as_any=True)
        except PydanticSerializationError as e:
            logger.critical(f'error serializing manifest: {e}')
            sys.exit(1)

        try:
            manifest_path.write_text(json_str)
        except OSError as e:
            logger.critical(f'error writing manifest file: {e}')
            sys.exit(1)

    def upload(self):
        """Upload the manifest to google cloud storage."""
        print('UPLOAD MANIFEST')

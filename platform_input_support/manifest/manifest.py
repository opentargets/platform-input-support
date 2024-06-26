import sys
import time
from datetime import datetime
from typing import TYPE_CHECKING

from loguru import logger
from pydantic import ValidationError
from pydantic_core import PydanticSerializationError

from platform_input_support.config import settings, steps
from platform_input_support.helpers import google_helper
from platform_input_support.manifest.models import RootManifest, StepManifest
from platform_input_support.manifest.util import recount
from platform_input_support.util.errors import HelperError, PISError, PreconditionFailedError
from platform_input_support.util.fs import get_full_path
from platform_input_support.util.misc import date_str

if TYPE_CHECKING:
    from platform_input_support.step import Step

MANIFEST_FILENAME = 'manifest.json'
UPLOAD_TIMEOUT = 3


class Manifest:
    def __init__(self):
        self._manifest: RootManifest
        self.generation: int
        self.relevant_step: Step

        self._init_manifest()

    def _init_manifest(self):
        manifest, generation = self._fetch_manifest()
        if not manifest:
            manifest = RootManifest()
            for step in steps():
                manifest.steps[step] = StepManifest(name=step)
        self._manifest = manifest
        self.generation = generation or 0

    def _fetch_manifest(self) -> tuple[RootManifest | None, int | None]:
        manifest_str: str | None = None
        generation: int | None = None

        # try fetching manifest from google cloud storage
        if google_helper().is_ready:
            manifest_path = f'{settings().gcs_url}/{MANIFEST_FILENAME}'
            try:
                manifest_str, generation = google_helper().download_to_string(manifest_path)
            except PISError:
                logger.warning('manifest file not found in gcs')

        # try fetching manifest from local file system
        if not manifest_str:
            manifest_path = get_full_path(MANIFEST_FILENAME)

            try:
                manifest_str = manifest_path.read_text()
            except FileNotFoundError:
                logger.warning(f'manifest file not found in {manifest_path}')
                return (None, None)
            except (OSError, PermissionError, ValueError) as e:
                logger.critical(f'error reading manifest file: {e}')
                sys.exit(1)

        try:
            manifest = RootManifest().model_validate_json(manifest_str)
        except ValidationError as e:
            logger.critical(f'error validating manifest file: {e}')
            sys.exit(1)

        logger.info(f'previous manifest found, last modified {date_str(manifest.modified)}')
        logger.trace(f'previous manifest generation = {generation}')
        return (manifest, generation)

    def update(self, step: 'Step'):
        self.relevant_step = step
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
        manifest_path = get_full_path(MANIFEST_FILENAME)

        logger.debug(f'uploading manifest to {settings().gcs_url}')

        uploaded = False
        while not uploaded:
            try:
                google_helper().upload_safe(
                    manifest_path,
                    f'{settings().gcs_url}/{MANIFEST_FILENAME}',
                    self.generation,
                )
                uploaded = True
            except PreconditionFailedError as e:
                logger.debug(f'{e}, retrying after {UPLOAD_TIMEOUT} seconds...')
                time.sleep(UPLOAD_TIMEOUT)

                # recreate manifest, fetching the latest version
                self._init_manifest()
                self.update(self.relevant_step)
                self.save()

            except HelperError as e:
                logger.critical(f'error uploading manifest file: {e}')
                sys.exit(1)

import sys
from functools import wraps
from typing import TYPE_CHECKING

from loguru import logger
from pydantic import ValidationError
from pydantic_core import PydanticSerializationError

from platform_input_support.config import settings
from platform_input_support.helpers import google_helper
from platform_input_support.manifest.models import RootManifest, Status
from platform_input_support.util.errors import PISError
from platform_input_support.util.misc import date_str, get_full_path

if TYPE_CHECKING:
    from platform_input_support.step import Step

MANIFEST_FILENAME = 'manifest.json'


class Manifest:
    def __init__(self):
        self._manifest = RootManifest()

    def _fetch_manifest(self) -> RootManifest | None:
        manifest_str: str | None = None

        # try fetching manifest from google cloud storage
        if google_helper.is_ready:
            manifest_path = f'{settings.gcs_url}/{MANIFEST_FILENAME}'
            try:
                manifest_str = google_helper.download(manifest_path)
            except PISError:
                logger.warning('manifest file not found in gcs')

        # try fetching manifest from local file system
        if not manifest_str:
            manifest_path = get_full_path(MANIFEST_FILENAME)

            try:
                manifest_str = manifest_path.read_text()
            except FileNotFoundError:
                logger.warning(f'manifest file not found in `{manifest_path}`')
                return None
            except (OSError, PermissionError, ValueError) as e:
                logger.critical(f'error reading manifest file: {e}')
                sys.exit(1)

        try:
            manifest = RootManifest().model_validate_json(manifest_str)
        except ValidationError as e:
            logger.critical(f'error validating manifest file: {e}')
            sys.exit(1)

        logger.success(f'previous manifest found: {date_str(manifest.modified)}')
        return manifest

    def _save_local_manifest(self):
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

    def end(self, step: 'Step'):
        self._manifest.steps[step.name] = step._manifest
        self._manifest.status = Status.COMPLETED
        for name, manifest in self._manifest.steps.items():
            if manifest.status is not Status.COMPLETED:
                self._manifest.status = Status.FAILED
                self._manifest.log.append(f'step `{name}` failed')

        self._save_local_manifest()


def report_to_manifest(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            if func.__name__ == 'run':
                # add custom fields from definition to the manifest
                self._manifest = self._manifest.model_copy(update=self.definition.__dict__, deep=True)

            result = func(self, *args, **kwargs)

            if func.__name__ == 'run':
                self.complete(result)
            elif func.__name__ == 'validate':
                self.pass_validation(result)
            return result
        except Exception as e:
            if func.__name__ == 'run':
                self.fail(e)
            elif func.__name__ == 'validate':
                self.fail_validation(e)

    return wrapper

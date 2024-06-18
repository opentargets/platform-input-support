import sys
from functools import wraps
from pathlib import Path

from loguru import logger
from pydantic import ValidationError
from pydantic_core import PydanticSerializationError

from platform_input_support.config import config
from platform_input_support.helpers import google_helper
from platform_input_support.manifest.models import RootManifest, Status, StepManifest

MANIFEST_FILENAME = 'manifest.json'


class Manifest:
    def __init__(self):
        self._manifest = self._fetch_manifest() or RootManifest()

    def _fetch_manifest(self) -> RootManifest | None:
        manifest_str: str | None = None
        manifest_path: str | Path = Path()

        # first, try fetching from google cloud storage
        if google_helper.is_ready:
            # gcs_url must be set, otherwise google.is_ready would be False
            assert config.gcs_url is not None
            manifest_path = f'{config.gcs_url}/{MANIFEST_FILENAME}'
            manifest_str = google_helper.download(manifest_path)
            if manifest_str is None:
                logger.warning('manifest file not found in gcs')
            # TODO CHECK THIS STUFF

        # then, try fetching from local file system
        if not manifest_str:
            manifest_path = Path(config.output_path) / MANIFEST_FILENAME

            try:
                manifest_str = manifest_path.read_text()
            except FileNotFoundError:
                logger.warning(f'manifest file not found in {manifest_path}')
                return None
            except (OSError, PermissionError, ValueError) as e:
                logger.critical(f'error reading manifest file: {e}')
                sys.exit(1)

        try:
            new_manifest = RootManifest().model_validate_json(manifest_str)
        except ValidationError as e:
            logger.critical(f'error validating manifest file: {e}')
            sys.exit(1)

        modified_date = new_manifest.modified.strftime('%Y-%m-%d %H:%M:%S')
        logger.success(f'manifest initialized, last modified {modified_date}')
        return new_manifest

    def _save_local_manifest(self):
        manifest_path = Path(config.output_path) / MANIFEST_FILENAME

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

    def get_step_manifest(self, name: str) -> StepManifest:
        return self._manifest.steps.get(name, StepManifest(name=name))

    # No typing here to avoid import mess, maybe when https://peps.python.org/pep-0649/ comes out
    def add_step(self, step):
        self._manifest.steps[step.name] = step._manifest

    def end(self, step_manifest: StepManifest):
        self._manifest.steps[step_manifest.name] = step_manifest
        self._manifest.status = Status.COMPLETED
        for previous_step_name, previous_step_manifest in self._manifest.steps.items():
            if previous_step_manifest.status is not Status.COMPLETED:
                self._manifest.status = Status.FAILED
                self._manifest.log.append(f'step {previous_step_name} failed')

        self._save_local_manifest()


def report_to_manifest(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            if func.__name__ == 'run':
                self.start()

                # add custom fields from config to the manifest
                self._manifest = self._manifest.model_copy(update=self.config.__dict__, deep=True)

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

"""Manifest class for managing the manifest file."""

import time
from datetime import datetime
from typing import TYPE_CHECKING

from filelock import FileLock, Timeout
from loguru import logger
from pydantic import ValidationError

from platform_input_support.config import settings, steps
from platform_input_support.helpers import google_helper
from platform_input_support.manifest.models import Result, RootManifest, StepManifest
from platform_input_support.manifest.util import recount
from platform_input_support.util.errors import (
    HelperError,
    NotFoundError,
    PISCriticalError,
    PreconditionFailedError,
)
from platform_input_support.util.fs import absolute_path
from platform_input_support.util.misc import date_str

if TYPE_CHECKING:
    from platform_input_support.step import Step

MANIFEST_FILENAME = 'manifest.json'
UPLOAD_TIMEOUT = 3


class Manifest:
    """Manifest class for managing the manifest file."""

    def __init__(self):
        self._manifest: RootManifest
        self._generation: int
        self._relevant_step_manifest: StepManifest

        self._init_manifest()

    def _init_manifest(self):
        manifest_str, self._generation = self._load_gcs() or self._load_local() or (None, 0)
        if manifest_str is None:
            self._manifest = self._create_empty()
            self._generation = 0
            logger.info('no prior manifest loaded')
        else:
            self._manifest = self._validate(manifest_str)
            logger.info(f'prior manifest loaded {date_str(self._manifest.modified)}')

    def _load_gcs(self) -> tuple[str, int] | None:
        if not google_helper().is_ready:
            raise PISCriticalError('google cloud storage helper did not initialize correctly')
        manifest_path = f'{settings().gcs_url}/{MANIFEST_FILENAME}'
        try:
            return google_helper().download_to_string(manifest_path)
        except NotFoundError:
            logger.info(f'no manifest file in {manifest_path}')
            return None

    def _load_local(self) -> tuple[str, int] | None:
        manifest_path = absolute_path(MANIFEST_FILENAME)
        try:
            return (manifest_path.read_text(), 0)
        except FileNotFoundError:
            logger.info(f'no manifest file in {manifest_path}')
            return None
        except (ValueError, OSError) as e:
            raise PISCriticalError(f'error reading manifest file: {e}')

    def _validate(self, manifest_str: str) -> RootManifest:
        try:
            return RootManifest().model_validate_json(manifest_str)
        except ValidationError as e:
            raise PISCriticalError(f'error validating manifest: {e}')

    def _create_empty(self) -> RootManifest:
        manifest = RootManifest()
        for step in steps():
            manifest.steps[step] = StepManifest(name=step)
        return manifest

    def _serialize(self) -> str:
        try:
            return self._manifest.model_dump_json(indent=2, serialize_as_any=True)
        except ValueError as e:
            raise PISCriticalError(f'error serializing manifest: {e}')

    def _save_local(self):
        manifest_path = absolute_path(MANIFEST_FILENAME)
        lock_path = f'{manifest_path}.lock'
        manifest_str = self._serialize()
        lock = FileLock(lock_path, timeout=5)
        try:
            lock.acquire()
            manifest_path.write_text(manifest_str)
            lock.release()
            logger.debug(f'manifest saved locally to {manifest_path}')
        except (OSError, Timeout) as e:
            raise PISCriticalError(f'error writing manifest file: {e}')

    def _refresh_from_gcs(self):
        self._init_manifest()
        self.update_step(self._relevant_step)
        self._save_local()

    def _save_gcs(self):
        uploaded = False
        blob_name = f'{settings().gcs_url}/{MANIFEST_FILENAME}'
        while not uploaded:
            try:
                google_helper().upload_safe(self._serialize(), blob_name, self._generation)
                uploaded = True
            except PreconditionFailedError as e:
                logger.debug(f'{e}, retrying after {UPLOAD_TIMEOUT} seconds...')
                time.sleep(UPLOAD_TIMEOUT)
                self._refresh_from_gcs()
            except HelperError as e:
                raise PISCriticalError(f'error uploading manifest: {e}')

    def update_step(self, step: 'Step'):
        """Update the manifest with the step.

        :param step: The step to update the manifest with.
        :type step: Step
        """
        self._relevant_step = step
        self._manifest.steps[step.name] = step._manifest
        self._manifest.modified = datetime.now()
        self._manifest.result = step._manifest.result
        recount(self._manifest)

    def complete(self):
        """Close the manifest and save it."""
        self._save_local()
        self._save_gcs()

        logger.info(f'manifest closed, result: {self._manifest.result}')

    def is_completed(self) -> bool:
        """Return whether the manifest is completed.

        :return: Whether the manifest is completed.
        :rtype: bool
        """
        return self._manifest.result == Result.COMPLETED

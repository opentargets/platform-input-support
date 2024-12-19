"""Manifest class for managing the manifest file."""

import time
from datetime import datetime
from typing import TYPE_CHECKING

from filelock import FileLock, Timeout
from loguru import logger
from pydantic import ValidationError

from pis.config import settings, steps
from pis.helpers.remote_storage import get_remote_storage
from pis.manifest.models import Result, RootManifest, StepManifest
from pis.manifest.util import recount
from pis.util.errors import (
    HelperError,
    NotFoundError,
    PISCriticalError,
    PreconditionFailedError,
    StorageError,
)
from pis.util.fs import absolute_path

if TYPE_CHECKING:
    from pis.step import Step

MANIFEST_FILENAME = 'manifest.json'
UPLOAD_COOLDOWN = 3


class Manifest:
    """Manifest class for managing the manifest file."""

    def __init__(self):
        self._remote_uri = f'{settings().remote_uri}/{MANIFEST_FILENAME}' if settings().remote_uri else None
        self._local_path = absolute_path(MANIFEST_FILENAME)
        self._revision = 0
        self._manifest = self._load_remote() or self._load_local() or self._create_empty()

    def _load_remote(self) -> RootManifest | None:
        if not self._remote_uri:
            logger.info('no remote URI provided, skipping remote manifest load')
            return None
        remote_storage = get_remote_storage(self._remote_uri)
        try:
            manifest_str, self._revision = remote_storage.download_to_string(self._remote_uri)
            logger.info(f'remote manifest read from {self._remote_uri}')
            return self._validate(manifest_str)
        except NotFoundError:
            logger.info(f'no remote manifest found in {self._remote_uri}')
            return None
        except StorageError as e:
            raise PISCriticalError(f'error reading manifest from {self._remote_uri}: {e}')

    def _load_local(self) -> RootManifest | None:
        try:
            manifest_str = self._local_path.read_text()
            logger.info(f'local manifest read from {self._local_path}')
            return self._validate(manifest_str)
        except FileNotFoundError:
            logger.info(f'no local manifest found in {self._local_path}')
            return None
        except (ValueError, OSError) as e:
            raise PISCriticalError(f'error reading manifest from {self._local_path}: {e}')

    def _create_empty(self) -> RootManifest:
        logger.info('creating empty manifest')
        manifest = RootManifest()
        for step in steps():
            manifest.steps[step] = StepManifest(name=step)
        return manifest

    def _validate(self, manifest_str: str) -> RootManifest:
        try:
            return RootManifest().model_validate_json(manifest_str)
        except ValidationError as e:
            raise PISCriticalError(f'error validating manifest: {e}')

    def _serialize(self) -> str:
        try:
            return self._manifest.model_dump_json(indent=2, serialize_as_any=True)
        except ValueError as e:
            raise PISCriticalError(f'error serializing manifest: {e}')

    def _refresh_from_remote(self):
        self._load_remote()
        self.update_step(self._relevant_step)
        self._save_local()

    def _save_remote(self):
        if not self._remote_uri:
            return
        uploaded = False
        remote_storage = get_remote_storage(self._remote_uri)
        while not uploaded:
            try:
                remote_storage.upload(self._local_path, self._remote_uri, self._revision)
                uploaded = True
            except PreconditionFailedError as e:
                logger.debug(f'{e}, retrying after {UPLOAD_COOLDOWN} seconds...')
                time.sleep(UPLOAD_COOLDOWN)
                self._refresh_from_remote()
            except HelperError as e:
                raise PISCriticalError(f'error uploading manifest: {e}')

    def _save_local(self):
        lock_path = f'{self._local_path}.lock'
        manifest_str = self._serialize()
        lock = FileLock(lock_path, timeout=5)
        try:
            lock.acquire()
            self._local_path.write_text(manifest_str)
            lock.release()
            logger.debug(f'local manifest {self._local_path} saved')
        except (OSError, Timeout) as e:
            raise PISCriticalError(f'error writing local manifest to {self._local_path}: {e}')

    def update_step(self, step: 'Step'):
        """Update the manifest with the step.

        :param step: The step to update the manifest with.
        :type step: Step
        """
        self._relevant_step = step
        self._manifest.steps[step.name] = step._manifest
        self._manifest.modified = datetime.now()
        recount(self._manifest)

    def complete(self):
        """Close the manifest and save it."""
        self._save_local()
        self._save_remote()

        logger.info(f'manifest closed, result: {self._manifest.result}')

    def run_ok(self) -> bool:
        """Return whether the run was successful.

        Note a successful run is defined as the step being in validated state if the
        run is local, or in complete state if the run has a remote URI.

        :return: Whether the run was successful.
        :rtype: bool
        """
        relevant_step_result = self._manifest.steps[self._relevant_step.name].result

        if settings().remote_uri:
            return relevant_step_result == Result.COMPLETED
        else:
            return relevant_step_result == Result.VALIDATED

    def is_completed(self) -> bool:
        """Return whether the manifest is completed.

        Note a successful run is defined as all steps in the manifest being in validated
        state if the run is local, or in complete state if the run has a remote URI.

        :return: Whether the manifest is completed.
        :rtype: bool
        """
        if settings().remote_uri:
            return self._manifest.result == Result.COMPLETED
        else:
            return self._manifest.result == Result.VALIDATED

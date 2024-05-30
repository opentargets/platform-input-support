import copy
import hashlib
import json
import logging
import os
from pathlib import Path

import google.auth
import jsonpickle
from google.cloud import exceptions, storage
from strenum import StrEnum

from platform_input_support.manifest import ManifestDocument, ManifestResource, ManifestStatus, ManifestStep
from platform_input_support.modules.common.time_utils import get_timestamp_iso_utc_now

# Logging
logger = logging.getLogger(__name__)

# Singleton
__manifestServiceInstance = None


def get_manifest_service(args=None, configuration=None):
    """Manifest Service factory method.

    Keyword Arguments:
        args -- configargparser args (default: {None})
        configuration -- config (default: {None})

    Returns:
        ManifestService instance
    """
    global __manifestServiceInstance  # noqa: PLW0603
    if __manifestServiceInstance is None:
        if configuration is None:
            msg = 'The Manifest subsystem has not been initialized and no configuration has been provided'
            logger.error(msg)
            raise ManifestServiceError(msg)
        manifest_config = configuration.config.manifest
        manifest_config.update({'output_dir': configuration.output_dir, 'gcp_bucket': args.gcp_bucket})
        logger.debug('Initializing Manifest service, configuration: %s', json.dumps(manifest_config))
        __manifestServiceInstance = ManifestService(manifest_config)
    return __manifestServiceInstance


class JsonEnumHandler(jsonpickle.handlers.BaseHandler):
    """Handler for ManifestStatus Enum."""

    def restore(self, obj):
        pass

    def flatten(self, obj: StrEnum, data):
        return obj.name


# Register the handler
jsonpickle.handlers.registry.register(ManifestStatus, JsonEnumHandler)


class GcpBucketService:
    """Google Cloud Platform bucket service.

    Get Google bucket objects and transfer data from them.
    """

    def __init__(self, bucket_name: str | None, path: str | None):
        """GCP bucket service constructor.

        Keyword Arguments:
            bucket_name -- GCP bucket name (default: {None})
            path -- GCP bucket path (default: {None})
        """
        self._logger = logging.getLogger(__name__)
        self.bucket_name = bucket_name
        self.path = path
        self.client = storage.Client()

    def get_bucket(self) -> storage.Bucket | None:
        """Get a Google bucket object if it exists.

        Returns:
            Bucket or None
        """
        if self.bucket_name is None:
            logger.error('No bucket name has been provided for this resource instance')
        else:
            try:
                return self.client.get_bucket(self.bucket_name)
            except google.cloud.exceptions.NotFound:
                logger.error('Bucket %s NOT FOUND', self.bucket_name)
            except exceptions.Forbidden:
                logger.error('Google Cloud Storage, FORBIDDEN access, path %s', self.bucket_name)
        return None

    def download_file(self, src_path_file: str, dst_path_file: str) -> None:
        """Download the contents of a google bucket (source) to a local file (dest).

        Arguments:
            src_path_file -- Source file path
            dst_path_file -- Destination file path
        """
        # WARNING - No error condition signaling mechanism is specified in the documentation
        self.get_bucket().blob(src_path_file).download_to_filename(dst_path_file)
        # TODO - Handle possible errors

    @staticmethod
    def get_bucket_and_path(google_bucket_param: str | None) -> tuple[None, None] | tuple[str, str]:
        """Get bucket and path from config param.

        Arguments:
            google_bucket_param -- google bucket config param

        Returns:
            gcp_bucket, gcp_path
        """
        if google_bucket_param is None:
            return None, None
        split = [*google_bucket_param.split('/', 1), None]
        return split[0], split[1]


class ManifestServiceError(Exception):
    """Manifest file exception class."""


class ManifestService:
    """This service manages the session's Manifest file."""

    def __init__(self, config):
        self.config = config
        self._logger = logging.getLogger(__name__)
        self.__manifest: ManifestDocument = None
        self.__is_manifest_loaded = False
        self.__resetted_manifest_steps = set()

    def __create_manifest(self) -> ManifestDocument:
        """Create a new ManifestDocument object."""
        return ManifestDocument(get_timestamp_iso_utc_now())

    def __create_manifest_step(self) -> ManifestStep:
        """Create a new ManifestStep object."""
        return ManifestStep(get_timestamp_iso_utc_now())

    def __load_manifest(self) -> ManifestDocument:
        """Load the manifest file if it exists, otherwise it will return None.

        :param manifest_file_path: The path to the manifest file
        :return: The manifest file object, None in case the file does not exist
        """
        # Check if the manifest file exists
        manifest_document = None
        if os.path.isfile(self.path_manifest):
            try:
                file_content = Path(self.path_manifest).read_text()
                manifest_document = jsonpickle.decode(file_content)  # noqa: S301
                self._logger.debug('Manifest file loaded from disk at %s', self.path_manifest)
            except Exception as e:
                self._logger.error('Error loading manifest file from disk at %s, error %s', self.path_manifest, e)
            else:
                self.__is_manifest_loaded = True
                # Load and modify the 'modified' timestamp
                manifest_document.modified = get_timestamp_iso_utc_now()
        # Return the manifest
        return manifest_document

    def _produce_manifest(self) -> ManifestDocument:
        """Produce the manifest file.

        The following precedence rules apply: local, GCP or create new one.
        """
        self._logger.debug('Local manifest file path at %s', self.path_manifest)
        if self.config.gcp_bucket is not None:
            gcp_bucket, gcp_path = GcpBucketService.get_bucket_and_path(self.config.gcp_bucket)
            gcp_path_manifest = f'{gcp_path}/{self.config.file_name}'
            gcp_client = GcpBucketService(gcp_bucket, gcp_path_manifest)
            gcp_bucket_full_path_manifest = f'{gcp_bucket}/{gcp_path_manifest}'
            try:
                logger.debug('GCP manifest file path %s', gcp_bucket_full_path_manifest)
                gcp_client.download_file(gcp_path_manifest, self.path_manifest)
            except Exception as e:
                self._logger.warning(
                    'GCP information provided but manifest file NOT FOUND at %s due to %s',
                    gcp_bucket_full_path_manifest,
                    e,
                )
            else:
                self._logger.debug('Loading existing manifest file at %s', gcp_bucket_full_path_manifest)
                return self.__load_manifest()
        manifest_document = self.__load_manifest()
        if manifest_document is None:
            self._logger.info('using NEW Manifest Document')
            manifest_document = self.__create_manifest()
        return manifest_document

    @property
    def path_manifest(self) -> str:
        """This property will return the path to the manifest file."""
        return os.path.join(self.config.output_dir, self.config.file_name)

    @property
    def manifest(self) -> ManifestDocument:
        if self.__manifest is None:
            self.__manifest = self._produce_manifest()
        return self.__manifest

    def make_paths_relative(self) -> None:
        """Make paths relative to the output directory."""
        self._logger.debug('Converting PATHs, relative to output dir')
        if self.manifest:
            for step in self.manifest.steps.values():
                self._logger.debug('Converting step %s PATHs', step.name)
                for resource in step.resources:
                    index_relative_path = resource.path_destination.rfind(self.config.output_dir)
                    if index_relative_path != -1:
                        index_relative_path += len(self.config.output_dir) + 1
                        resource.path_destination = resource.path_destination[index_relative_path:]

    def __reset_manifest_step(self, step_name: str) -> None:
        """Reset manifest step.

        When repeating a step we need to overwrite the existing instance of
        that step in the manifest. This method is used to reset the state of
        that step to the initial state.

        Arguments:
            step_name -- step to reset
        """
        self._logger.debug('Reset request for step name %s', step_name)
        if step_name not in self.__resetted_manifest_steps:
            self._logger.debug('Resetting step %s', step_name)
            new_manifest_step = self.__create_manifest_step()
            new_manifest_step.name = step_name
            new_manifest_step.created = self.manifest.steps[step_name].created
            self.manifest.steps[step_name] = new_manifest_step
            self.__resetted_manifest_steps.add(step_name)

    def _reset_manifest_document_statuses(self) -> None:
        """Reset manifest document statuses to defaults."""
        self._logger.debug('resetting manifest defaults')
        self.manifest.status = ManifestStatus.FAILED
        self.manifest.status_completion = ManifestStatus.NOT_COMPLETED
        self.manifest.msg_completion = ManifestStatus.NOT_SET

    def get_step(self, step_name: str = 'ANONYMOUS') -> ManifestStep:
        if step_name not in self.manifest.steps:
            self.manifest.steps[step_name] = self.__create_manifest_step()
            self.manifest.steps[step_name].name = step_name
        elif self.__is_manifest_loaded:
            # When the manifest file has been loaded from a file, we need to empty the resources in a given step
            #  the first time that step's metadata is accessed
            self.__reset_manifest_step(step_name)
        return self.manifest.steps[step_name]

    def new_resource(self) -> ManifestResource:
        """Return a new manifest resource."""
        return ManifestResource(get_timestamp_iso_utc_now())

    @staticmethod
    def _get_checksum_compute_chain() -> dict:
        """Return a dictionary of checksums.

        Returns:
            Dict of checksums
        """
        return {'md5sum': hashlib.md5(), 'sha256sum': hashlib.sha256()}

    @staticmethod
    def clone_resource(resource: ManifestResource) -> ManifestResource:
        return copy.copy(resource)

    @staticmethod
    def are_all_resources_complete(resources: list[ManifestResource]) -> bool:
        return all(resource.status_completion == ManifestStatus.COMPLETED for resource in resources)

    @staticmethod
    def are_all_steps_complete(steps: list[ManifestStep]) -> bool:
        # TODO - Refactor into a single method that accepts either ManifestResource or ManifestStatus
        return all(step.status_completion == ManifestStatus.COMPLETED for step in steps)

    def _compute_checksums_for_resource(self, resource: ManifestResource) -> tuple[bool, list[str], ManifestResource]:
        """Compute checksums for the specified resource.

        Arguments:
            resource -- Manifest resourece to compute checksums for

        Returns:
            Tuple[
                success status (bool),
                errors (List),
                ManifestResource
                ]
        """
        self._logger.debug('Computing checksums for %s', resource.path_destination)
        success = False
        errors = []
        buf_size = 65536
        hashers = self._get_checksum_compute_chain()
        # TODO - Handle possible errors
        with open(resource.path_destination, 'rb') as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                for hasher in hashers.values():
                    hasher.update(data)
        for hasher_key, hasher in hashers.items():
            setattr(resource.destination_checksums, hasher_key, hasher.hexdigest())
            self._logger.debug(
                '%s -> %s(%s)',
                resource.path_destination,
                hasher_key,
                getattr(resource.destination_checksums, hasher_key),
            )

        success = True
        return success, errors, resource

    def compute_checksums(self, resources: list[ManifestResource]) -> int:
        """Compute checksums for resources.

        Arguments:
            resources -- List of manifest resources

        Returns:
            Number of successfully computed checksums
        """
        self._logger.debug('[CHECKSUMS] Computing for %s resources', len(resources))
        n_success = 0
        for resource in resources:
            # TODO - Handle errors
            if resource.status_completion == ManifestStatus.COMPLETED:
                success, _, _ = self._compute_checksums_for_resource(resource)
                if success:
                    n_success += 1
        self._logger.debug('[CHECKSUMS] Completed')
        return n_success

    def add_resource_to_step(self, step_name: str, resource: ManifestResource) -> None:
        """Add ManifestResource to step.

        Arguments:
            step_name -- Name of step to add the resource to
            resource -- Resource to add
        """
        manifest_step = self.get_step(step_name)
        manifest_step.resources.append(resource)

    def persist(self) -> None:
        """Persist the manifest file to the output directory."""
        self.make_paths_relative()
        try:
            enconded_json = jsonpickle.encode(self.manifest, make_refs=False)
            Path(self.path_manifest).write_text(enconded_json)
        except OSError:
            self._logger.error('COULD NOT write manifest file %s', self.path_manifest)
        self._logger.info('WROTE manifest file %s, session %s', self.path_manifest, self.manifest.session)

    def evaluate_manifest_document(self) -> None:
        """Evaluate the statuses based on the manifest steps statuses."""
        # Evaluate statuses
        if self.__is_manifest_loaded:
            self._reset_manifest_document_statuses()
        self.manifest.msg_completion = ManifestStatus.NOT_SET
        if not self.are_all_steps_complete(self.manifest.steps.values()):
            self.manifest.status_completion = ManifestStatus.FAILED
            self.manifest.msg_completion = 'COULD NOT complete data collection for one or more steps'
        # TODO - Pipeline level VALIDATION
        if self.manifest.status_completion != ManifestStatus.FAILED:
            self.manifest.status_completion = ManifestStatus.COMPLETED
            self.manifest.status = ManifestStatus.COMPLETED
            self.manifest.msg_completion = 'All steps completed their data collection'
        else:
            logger.error(self.manifest.msg_completion)

import hashlib
import itertools
import os
import json
import copy
import logging
import jsonpickle
import google.auth
import multiprocessing as mp
from strenum import StrEnum
from google.cloud import storage, exceptions
from typing import List, Tuple

from modules.common.TimeUtils import get_timestamp_iso_utc_now
from .models import ManifestStep, ManifestResource, ManifestDocument, ManifestStatus

# Logging
logger = logging.getLogger(__name__)

# Singleton
__manifestServiceInstance = None


def get_manifest_service(args=None, configuration=None):
    """
    Manifest Service factory method
    """
    global __manifestServiceInstance
    if __manifestServiceInstance is None:
        if configuration is None:
            msg = "The Manifest subsystem has not been initialized and no configuration has been provided"
            logger.error(msg)
            raise ManifestServiceException(msg)
        manifest_config = configuration.config.manifest
        manifest_config.update({"output_dir": configuration.output_dir, "gcp_bucket": args.gcp_bucket})
        logger.debug("Initializing Manifest service, configuration: {}".format(json.dumps(manifest_config)))
        __manifestServiceInstance = ManifestService(manifest_config)
    return __manifestServiceInstance

# Handler for ManifestStatus Enum
class JsonEnumHandler(jsonpickle.handlers.BaseHandler):
    def restore(self, obj):
        pass

    def flatten(self, obj: StrEnum, data):
        return obj.name


# Register the handler
jsonpickle.handlers.registry.register(ManifestStatus, JsonEnumHandler)


class GcpBucketService(object):
    def __init__(self, bucket_name=None, path=None):
        self._logger = logging.getLogger(__name__)
        self.bucket_name = bucket_name
        self.path = path
        self.client = storage.Client()

    def get_bucket(self):
        if self.bucket_name is None:
            logger.error("No bucket name has been provided for this resource instance")
        else:
            try:
                bucket = self.client.get_bucket(self.bucket_name)
                return bucket
            except google.cloud.exceptions.NotFound:
                logger.error("Bucket '{}' NOT FOUND".format(self.bucket_name))
            except exceptions.Forbidden:
                logger.error("Google Cloud Storage, FORBIDDEN access, path '{}'".format(self.bucket_name))
        return None

    def download_file(self, src_path_file, dst_path_file):
        # WARNING - No error condition signaling mechanism is specified in the documentation
        self.get_bucket() \
            .blob(src_path_file) \
            .download_to_filename(dst_path_file)
        # TODO - Handle possible errors

    @staticmethod
    def get_bucket_and_path(google_bucket_param):
        if google_bucket_param is None:
            return None, None
        split = google_bucket_param.split('/', 1) + [None]
        return split[0], split[1]


class ManifestServiceException(Exception):
    """
    Exception type for errors dealing with the manifest file
    """
    pass


class ManifestService():
    """
    This service manages the session's Manifest file
    """

    def __init__(self, config):
        self.config = config
        self.session_timestamp: str = get_timestamp_iso_utc_now()
        self._logger = logging.getLogger(__name__)
        self.__manifest: ManifestDocument = None
        self.__is_manifest_loaded = False

    def __create_manifest(self) -> ManifestDocument:
        manifest_document = ManifestDocument(self.session_timestamp)
        return manifest_document

    def __create_manifest_step(self) -> ManifestStep:
        return ManifestStep(self.session_timestamp)

    def __load_manifest(self) -> ManifestDocument:
        # TODO
        # Load and modify the 'modified' timestamp
        self.__is_manifest_loaded = True
        raise NotImplementedError("Loading a manifest document from a file is not supported yet")

    def _produce_manifest(self) -> ManifestDocument:
        """
        This method will produce the manifest file with the following precedence rules: local, GCP or create new one
        """
        self._logger.debug(f"Local manifest file path '{self.path_manifest}'")
        if os.path.isfile(self.path_manifest):
            self._logger.info(f"Loading existing manifest file at '{self.path_manifest}'")
            return self.__load_manifest()
        if self.config.gcp_bucket is not None:
            gcp_bucket, gcp_path = GcpBucketService.get_bucket_and_path(self.config.gcp_bucket)
            gcp_path_manifest = f"{gcp_path}/{self.config.file_name}"
            gcp_client = GcpBucketService(gcp_bucket, gcp_path_manifest)
            gcp_bucket_full_path_manifest = f"{gcp_bucket}/{gcp_path_manifest}"
            try:
                logger.debug(f"GCP manifest file path '{gcp_bucket_full_path_manifest}'")
                gcp_client.download_file(gcp_path_manifest, self.path_manifest)
            except Exception as e:
                self._logger.warning(
                    f"GCP information provided, "
                    f"but manifest file NOT FOUND at '{gcp_bucket_full_path_manifest}', "
                    f"due to '{e}'")
            else:
                self._logger.debug(f"Loading existing manifest file at '{gcp_bucket_full_path_manifest}'")
                return self.__load_manifest()
        self._logger.info("using NEW Manifest Document")
        return self.__create_manifest()

    @property
    def path_manifest(self) -> str:
        return os.path.join(self.config.output_dir, self.config.file_name)

    @property
    def manifest(self) -> ManifestDocument:
        if self.__manifest is None:
            self.__manifest = self._produce_manifest()
        return self.__manifest

    def make_paths_relative(self):
        self._logger.debug("Converting PATHs, relative to output dir")
        if self.manifest:
            for step in self.manifest.steps.values():
                self._logger.debug(f"Converting step '{step.name}' PATHs")
                for resource in step.resources:
                    index_relative_path = resource.path_destination.rfind(self.config.output_dir)
                    if index_relative_path != -1:
                        index_relative_path += len(self.config.output_dir) + 1
                        resource.path_destination = resource.path_destination[index_relative_path:]

    def get_step(self, step_name: str = "ANONYMOUS") -> ManifestStep:
        if step_name not in self.manifest.steps:
            self.manifest.steps[step_name] = self.__create_manifest_step()
            self.manifest.steps[step_name].name = step_name
        if self.__is_manifest_loaded:
            # TODO - When the manifest file has been loaded from a file, we need to empty the resources in a given step
            #  the first time that step's metadata is accessed
            self.manifest.steps[step_name].modified = get_timestamp_iso_utc_now()
        return self.manifest.steps[step_name]

    def new_resource(self) -> ManifestResource:
        return ManifestResource(get_timestamp_iso_utc_now())

    @staticmethod
    def _get_checksum_compute_chain():
        return {
            'md5sum': hashlib.md5(),
            'sha256sum': hashlib.sha256()
        }

    @staticmethod
    def clone_resource(resource: ManifestResource) -> ManifestResource:
        return copy.copy(resource)

    def _compute_checksums_for_resource(self, resource: ManifestResource) -> Tuple[bool, List[str], ManifestResource]:
        self._logger.debug(f"Computing checksums for '{resource.path_destination}'")
        success = False
        errors = []
        BUF_SIZE = 65536
        hashers = self._get_checksum_compute_chain()
        # TODO - Handle possible errors
        with open(resource.path_destination, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                for hasher_key, hasher in hashers.items():
                    hasher.update(data)
        for hasher_key, hasher in hashers.items():
            setattr(resource.destination_checksums, hasher_key, hasher.hexdigest())
            self._logger.debug(
                f"{resource.path_destination} -> {hasher_key}({getattr(resource.destination_checksums, hasher_key)})"
            )
        success = True
        return (success, errors, resource)

    def compute_checksums(self, resources: List[ManifestResource]) -> int:
        self._logger.debug(f"[CHECKSUMS] Computing for {len(resources)} resources")
        n_success = 0
        for resource in resources:
            # TODO - Handle errors
            success, errors, _ = self._compute_checksums_for_resource(resource)
            if success:
                n_success += 1
        self._logger.debug(f"[CHECKSUMS] Completed")
        return n_success

    def add_resource_to_step(self, step_name: str, resource: ManifestResource):
        manifest_step = self.get_step(step_name)
        manifest_step.resources.append(resource)

    def persist(self):
        # TODO - Checksums computation should be triggered by each step, so they are available for validators
        self.compute_checksums(
            list(itertools.chain.from_iterable([step.resources for step in self.manifest.steps.values()]))
        )
        self.make_paths_relative()
        try:
            with open(self.path_manifest, 'w') as fmanifest:
                fmanifest.write(jsonpickle.encode(self.manifest, make_refs=False))
        except EnvironmentError as e:
            self._logger.error(f"COULD NOT write manifest file '{self.path_manifest}'")
        self._logger.info(f"WROTE manifest file '{self.path_manifest}', session '{self.manifest.session}'")

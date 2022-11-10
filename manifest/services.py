import os
import json
import logging
import jsonpickle
from strenum import StrEnum
from modules.common.GoogleBucketResource import GoogleBucketResource
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
            gcp_bucket, gcp_path = GoogleBucketResource.get_bucket_and_path(self.config.gcp_bucket)
            gcp_path_manifest = f"{gcp_path}/{self.config.file_name}"
            gcp_client = GoogleBucketResource(gcp_bucket, gcp_path_manifest)
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

    def add_resource_to_step(self, step_name: str, resource: ManifestResource):
        manifest_step = self.get_step(step_name)
        manifest_step.resources.append(resource)

    def persist(self):
        try:
            with open(self.path_manifest, 'w') as fmanifest:
                fmanifest.write(jsonpickle.encode(self.manifest, make_refs=False))
        except EnvironmentError as e:
            self._logger.error(f"COULD NOT write manifest file '{self.path_manifest}'")
        self._logger.info(f"WROTE manifest file '{self.path_manifest}', session '{self.manifest.session}'")

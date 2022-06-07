import os
import time
import json
import logging
from .models import ManifestStep, ManifestResource, ManifestDocument

# Logging
logger = logging.getLogger(__name__)

# Singleton
__manifestServiceInstance = None


def get_manifest_service(args=None, configuration=None):
    global __manifestServiceInstance
    if __manifestServiceInstance is None:
        if configuration is None:
            msg = "The Manifest subsystem has not been initialized and no configuration has been provided"
            logger.error(msg)
            raise ManifestServiceException(msg)
        else:
            manifest_config = configuration.config.manifest
            manifest_config.update({"output_dir": args.output_dir})
            logger.debug("Initializing Manifest service, configuration: {}".format(json.dumps(manifest_config)))
            __manifestServiceInstance = ManifestService(manifest_config)
    return __manifestServiceInstance


class ManifestServiceException(Exception):
    """
    Exception type for errors dealing with the manifest file
    """
    pass


class ManifestService:
    """
    This service manages the session's Manifest file
    """

    def __init__(self, config):
        self.__manifest :ManifestDocument = None
        self.config = config
        self.session_timestamp :float = time.time()
        # TODO

    def __create_manifest(self) -> ManifestDocument:
        manifest_document = ManifestDocument()
        manifest_document.session = self.session_timestamp
        return manifest_document

    def __load_or_create_manifest(self) -> ManifestDocument:
        self.__manifest = self.__create_manifest()
        # TODO Option - Copy from remote
        # TODO Overwrite with locally
        pass

    @property
    def path_manifest(self) -> str:
        return os.path.join(self.config.output_dir, self.config.file_name)

    @property
    def manifest(self) -> ManifestDocument:
        if self.__manifest is None:
            self.__manifest = self.__load_or_create_manifest()
        return self.__manifest

    def get_step(self, step_name: str) -> ManifestStep:
        pass

    def create_resource(self) -> ManifestResource:
        pass

    def persist(self):
        pass

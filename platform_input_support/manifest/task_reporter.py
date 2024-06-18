from loguru import logger

from platform_input_support.manifest.models import Status, TaskManifest


class TaskReporter:
    def __init__(self, name: str):
        self.name = name
        self._manifest: TaskManifest

    def attach_manifest(self, manifest: TaskManifest):
        logger.debug(f'attached manifest to task {self.name}')
        self._manifest = manifest

    def start(self):
        logger.info('starting task')
        self._manifest.status = Status.NOT_COMPLETED

    def complete(self, log: str):
        self._manifest.log.append(log)
        self._manifest.status = Status.COMPLETED
        logger.success(f'task completed: {log}')

    def fail(self, error: Exception):
        self._manifest.log.append(str(error))
        self._manifest.status = Status.FAILED
        logger.error(f'task failed: {error}')

    def pass_validation(self, log: str):
        self._manifest.log.append(log)
        self._manifest.status = Status.VALIDATION_PASSED
        logger.success('validation passed')

    def fail_validation(self, error: Exception):
        self._manifest.log.append(str(error))
        self._manifest.status = Status.VALIDATION_FAILED
        logger.error(f'failed validation: f{error}')

    def append_log(self, log: str):
        logger.info(log)
        self._manifest.log.append(log)

    def set_field(self, field_name: str, value: str):
        setattr(self._manifest, field_name, value)

    def must_run(self) -> bool:
        return self._manifest.status not in [Status.COMPLETED, Status.VALIDATION_PASSED]

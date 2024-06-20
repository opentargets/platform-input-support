from loguru import logger

from platform_input_support.manifest.models import Status, TaskManifest


class TaskReporter:
    def __init__(self, name: str):
        self.name = name
        self._manifest: TaskManifest

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
        logger.error(f'failed validation: {error}')

    def append_log(self, log: str):
        logger.info(log)
        self._manifest.log.append(log)

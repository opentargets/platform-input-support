from datetime import datetime

from platform_input_support.manifest.models import ManifestReport, PartReport, ResourceReport, Status, StepReport


class ManifestReporter:
    def __init__(self):
        self._manifest = ManifestReport()

    def start_manifest(self):
        self._manifest.modified = datetime.now()
        self._manifest.status = Status.NOT_COMPLETED

    def pass_manifest(self):
        self._manifest.status = Status.COMPLETED

    def fail_manifest(self, msg: str | None):
        if msg:
            self._manifest.log.append(msg)

        self._manifest.status = Status.FAILED

    def validate_manifest(self):
        self._manifest.status = Status.VALIDATED

    def fail_validation_manifest(self, msg: str | None):
        if msg:
            self._manifest.log.append(msg)

        self._manifest.status = Status.VALIDATION_FAILED

    def new_step(self, step_name: str) -> StepReport:
        step = StepReport(name=step_name)
        self._manifest.steps[step.name] = step
        return step


class StepReporter:
    def __init__(self):
        self._step = StepReport()

    def start_step(self):
        step_name = self.__class__.__name__.lower()
        self._step = StepReport(name=step_name)

    def pass_step(self):
        self._step.status = Status.COMPLETED

    def fail_step(self, msg: str | None):
        if msg:
            self._step.log.append(msg)

        self._step.status = Status.FAILED

    def validate_step(self):
        self._step.status = Status.VALIDATED

    def fail_validation_step(self, msg: str | None):
        if msg:
            self._step.log.append(msg)

        self._step.status = Status.VALIDATION_FAILED

    def new_part(self) -> PartReport:
        resource = PartReport()
        self._step.parts.append(resource)
        return resource


class ResourceReporter:
    def __init__(self):
        self._resource = ResourceReport()

    def start_resource(self, source_url, destination_path):
        self._resource.source_url = source_url
        self._resource.status = Status.NOT_COMPLETED
        self._resource.destination_path = destination_path

    def pass_resource(self):
        self._resource.status = Status.COMPLETED

    def fail_resource(self, msg: str | None):
        if msg:
            self._resource.log.append(msg)

        self._resource.status = Status.FAILED

    def validate_resource(self, checksum_destination, checksum_source):
        self._resource.checksum_destination = checksum_destination
        self._resource.checksum_source = checksum_source
        self._resource.status = Status.VALIDATED

    def fail_validation_resource(self, checksum_destination, checksum_source, msg: str | None):
        self._resource.checksum_destination = checksum_destination
        self._resource.checksum_source = checksum_source
        if msg:
            self._resource.log.append(msg)

        self._resource.status = Status.VALIDATION_FAILED

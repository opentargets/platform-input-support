import datetime
from dataclasses import dataclass, field
from enum import auto

from strenum import StrEnum


class Status(StrEnum):
    NOT_SET = auto()
    NOT_COMPLETED = auto()
    FAILED = auto()
    COMPLETED = auto()
    VALIDATION_FAILED = auto()
    VALIDATION_PASSED = auto()


@dataclass
class ActionReport:
    name: str | Status = Status.NOT_SET
    status: Status = Status.NOT_COMPLETED
    created: datetime.datetime = field(default_factory=datetime.datetime.now)
    log: list[str] = field(default_factory=list)


@dataclass
class StepReport:
    name: str | Status = Status.NOT_SET
    status: Status = Status.NOT_COMPLETED
    actions: list[ActionReport] = field(default_factory=list)
    created: datetime.datetime = field(default_factory=datetime.datetime.now)
    modified: datetime.datetime = field(default_factory=datetime.datetime.now)
    log: list[str] = field(default_factory=list)


@dataclass
class ManifestReport:
    status: Status = Status.NOT_SET
    steps: dict[str, StepReport] = field(default_factory=dict)
    created: datetime.datetime = field(default_factory=datetime.datetime.now)
    modified: datetime.datetime = field(default_factory=datetime.datetime.now)
    log: list[str] = field(default_factory=list)


@dataclass
class ResourceReport(ActionReport):
    source_url: str | Status = Status.NOT_SET
    destination_path: str | Status = Status.NOT_SET
    checksum_destination: str | Status = Status.NOT_SET
    checksum_source: str | Status = Status.NOT_SET

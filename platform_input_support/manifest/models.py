import datetime
from dataclasses import dataclass, field
from enum import StrEnum, auto


class Status(StrEnum):
    NOT_SET = auto()
    NOT_COMPLETED = auto()
    FAILED = auto()
    COMPLETED = auto()
    VALIDATION_FAILED = auto()
    VALIDATION_PASSED = auto()


@dataclass
class TaskReport:
    name: str | Status = Status.NOT_SET
    status: Status = Status.NOT_COMPLETED
    created: datetime.datetime = field(default_factory=datetime.datetime.now)
    log: list[str] = field(default_factory=list)


@dataclass
class StepReport:
    name: str | Status = Status.NOT_SET
    status: Status = Status.NOT_COMPLETED
    tasks: list[TaskReport] = field(default_factory=list)
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

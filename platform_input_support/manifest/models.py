from datetime import UTC, datetime
from enum import StrEnum, auto

from pydantic import BaseModel, ConfigDict


class Status(StrEnum):
    NOT_SET = auto()
    NOT_COMPLETED = auto()
    FAILED = auto()
    COMPLETED = auto()
    VALIDATION_FAILED = auto()
    VALIDATION_PASSED = auto()


class TaskManifest(BaseModel):
    name: str
    status: Status = Status.NOT_COMPLETED
    created: datetime = datetime.now(UTC)
    log: list[str] = []

    model_config = ConfigDict(extra='allow')


class StepManifest(BaseModel):
    name: str
    status: Status = Status.NOT_COMPLETED
    created: datetime = datetime.now(UTC)
    modified: datetime = datetime.now(UTC)
    log: list[str] = []
    tasks: list[TaskManifest] = []


class RootManifest(BaseModel):
    status: Status = Status.NOT_COMPLETED
    created: datetime = datetime.now(UTC)
    modified: datetime = datetime.now(UTC)
    log: list[str] = []
    steps: dict[str, StepManifest] = {}

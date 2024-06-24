from datetime import UTC, datetime
from enum import StrEnum, auto
from typing import Any

from pydantic import BaseModel


class Status(StrEnum):
    NOT_COMPLETED = auto()
    ABORTED = auto()
    FAILED = auto()
    COMPLETED = auto()
    VALIDATION_FAILED = auto()
    VALIDATION_PASSED = auto()


class TaskManifest(BaseModel, extra='allow'):
    name: str
    definition: dict[str, Any] = {}
    status: Status = Status.NOT_COMPLETED
    created: datetime = datetime.now(UTC)
    log: list[str] = []


class StepManifest(BaseModel):
    name: str
    status: Status = Status.NOT_COMPLETED
    created: datetime = datetime.now(UTC)
    log: list[str] = []
    tasks: list[TaskManifest] = []


class RootManifest(BaseModel):
    status: Status = Status.NOT_COMPLETED
    created: datetime = datetime.now(UTC)
    modified: datetime = datetime.now(UTC)
    log: list[str] = []
    steps: dict[str, StepManifest] = {}

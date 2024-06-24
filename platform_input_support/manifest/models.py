from datetime import UTC, datetime
from enum import StrEnum, auto
from typing import Any

from pydantic import BaseModel


class Result(StrEnum):
    # fmt: off
    PENDING = auto()    # step or task has not started
    STAGED = auto()     # step or task has been staged
    COMPLETED = auto()  # step or task has completed successfully
    VALIDATED = auto()  # step or task has passed validation
    FAILED = auto()     # step or task failed
    ABORTED = auto()    # step or task was aborted


class TaskManifest(BaseModel, extra='allow'):
    name: str
    result: Result = Result.PENDING
    created: datetime = datetime.now(UTC)
    log: list[str] = []
    definition: dict[str, Any] = {}


class StepManifest(BaseModel):
    name: str
    result: Result = Result.PENDING
    created: datetime = datetime.now(UTC)
    log: list[str] = []
    tasks: list[TaskManifest] = []


class RootManifest(BaseModel):
    result: Result = Result.PENDING
    created: datetime = datetime.now(UTC)
    modified: datetime = datetime.now(UTC)
    log: list[str] = []
    steps: dict[str, StepManifest] = {}

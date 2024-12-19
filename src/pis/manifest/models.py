"""Manifest data models."""

from datetime import UTC, datetime
from enum import StrEnum, auto
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from pis.config import settings


class Result(StrEnum):
    """Result enumeration.

    The result of a task or step. See :class:`TaskManifest` and :class:`StepManifest`.
    """

    # fmt: off
    PENDING = auto()
    STAGED = auto()
    VALIDATED = auto()
    COMPLETED = auto()
    FAILED = auto()
    ABORTED = auto()


class Resource(BaseModel):
    """Resource model.

    A resource is the resulting file or files from a task. All tasks must produce a
    resource, and it will be logged into the manifest for tracking.
    """

    source: str
    destination: str

    def make_absolute(self) -> 'Resource':
        """Make the destination path absolute."""
        if base_uri := settings().remote_uri:
            abs_destination = f'{base_uri}/{self.destination}'
        else:
            abs_destination = Path(self.destination).absolute().as_posix()
        return Resource(source=self.source, destination=abs_destination)


class TaskManifest(BaseModel, extra='allow'):
    """Model for a task in a step of the manifest."""

    name: str
    result: Result = Result.PENDING
    created: datetime = datetime.now(UTC)
    staged: datetime = datetime.now(UTC)
    elapsed: float = 0.0
    log: list[str] = []
    definition: dict[str, Any] = {}


class StepManifest(BaseModel):
    """Model for a step in the manifest."""

    name: str
    result: Result = Result.PENDING
    created: datetime = datetime.now(UTC)
    completed: datetime | None = None
    elapsed: float = 0.0
    log: list[str] = []
    tasks: list[TaskManifest] = []
    resources: list[Resource] = []


class RootManifest(BaseModel):
    """Model for the root of the manifest."""

    result: Result = Result.PENDING
    created: datetime = datetime.now(UTC)
    modified: datetime = datetime.now(UTC)
    log: list[str] = []
    steps: dict[str, StepManifest] = {}  # The steps of the manifest.

"""Manifest file data models.

The Manifest file stores the state of the PIS pipeline.
The file is organised like so:
- pipeline status/completion/messages
- pipeline timestamp
- steps
  - step status/completion/messages
  - step name/timestamp
  - resources
    - resource status/completion/messages
    - resource timestamp
    - resource checksum
The key terms here are:
- _pipeline_: The overall pipeline represented by the ManifestDocument class.
- _step_:     There are many steps in the pipeline e.g. evidence or disease,
              represented by the ManifestStep class.
- _resource_: There are many resources in each step, which repesent each data
              source required for that step and represented by the
              ManifestResource class.
The pipeline status is evaluated on the status of it's steps, which in turn
are evaluated on their resources. So, if the pipeline status is a fail,
that means one or more of the steps have failed.
In turn, a step will have failed because one or more of it's resources have
failed.
"""

import logging
from enum import auto

from strenum import StrEnum

from platform_input_support.modules.common.time_utils import get_timestamp_iso_utc_now

# Logging
logger = logging.getLogger(__name__)


class ManifestDocument:
    """Top-level data model for manifest document.

    Represents the state of the overall pipeline, when it was
    created/modified. What the overal status of the pipeline is with
    messages and a list of steps objects [ManifestStep].
    """

    def __init__(self, timestamp: str | None = None):
        """Manifest file root content constructor.

        Keyword Arguments:
            timestamp -- ISO format timestamp string (default: {None})
        """
        if timestamp is None:
            timestamp = get_timestamp_iso_utc_now()
        self.session: str = timestamp
        self.created: str = timestamp
        self.modified: str = timestamp
        self.steps: dict[str, ManifestStep] = {}
        self.status: str = ManifestStatus.FAILED
        self.status_completion: str = ManifestStatus.NOT_COMPLETED
        self.status_validation: str = ManifestStatus.NOT_VALIDATED
        self.msg_completion: str = ManifestStatus.NOT_SET
        self.msg_validation: str = ManifestStatus.NOT_SET


class ManifestStep:
    """Data model for manifest step.

    Represents the state of a step e.g. 'evidence' step or 'disease' step
    in the pipeline. With a timestamp for time created/modified,
    the name of the step and the completion status and message.
    It also lists the step's resources [ManifestResource].
    """

    def __init__(self, timestamp: str | None = None):
        """Manifest file root content constructor.

        Keyword Arguments:
            timestamp -- ISO format timestamp string (default: {None})
        """
        if timestamp is None:
            timestamp = get_timestamp_iso_utc_now()
        self.created: str = timestamp
        self.modified: str = timestamp
        self.name: str = ManifestStatus.NO_NAME
        self.resources: list = []
        self.status_completion: str = ManifestStatus.NOT_COMPLETED
        self.status_validation: str = ManifestStatus.NOT_VALIDATED
        self.msg_completion: str = ManifestStatus.NOT_SET
        self.msg_validation: str = ManifestStatus.NOT_SET


class ManifestResource:
    """Data model for manifest resource.

    Represents the state of a single resource. Includes the timestamp for
    when it was create, the resource source and desination, the completion
    status and the checksums for that resource [ManifestResourceChecksums].
    """

    def __init__(self, timestamp: str | None = None):
        """Manifest file root content constructor.

        Keyword Arguments:
            timestamp -- ISO format timestamp string (default: {None})
        """
        if timestamp is None:
            timestamp = get_timestamp_iso_utc_now()
        self.created: str = timestamp
        self.source_url: str = ManifestStatus.NOT_SET
        self.path_destination: str = ManifestStatus.NOT_SET
        self.status_completion: str = ManifestStatus.NOT_COMPLETED
        self.status_validation: str = ManifestStatus.NOT_VALIDATED
        self.msg_completion: str = ManifestStatus.NOT_SET
        self.msg_validation: str = ManifestStatus.NOT_SET
        self.source_checksums = ManifestResourceChecksums()
        self.destination_checksums = ManifestResourceChecksums()


class ManifestResourceChecksums:
    """Data model for manifest resource checksums."""

    def __init__(self):
        self.crc32 = ManifestStatus.NOT_SET
        self.md5sum = ManifestStatus.NOT_SET
        self.sha256sum = ManifestStatus.NOT_SET


class ManifestStatus(StrEnum):
    """Manifest status enums."""

    ERROR = auto()
    FAILED = auto()
    NO_NAME = auto()
    UNKNOWN = auto()
    SUCCESS = auto()
    INVALID = auto()
    NOT_SET = auto()
    COMPLETED = auto()
    NOT_PROVIDED = auto()
    NOT_COMPLETED = auto()
    NOT_VALIDATED = auto()

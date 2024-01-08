# Manifest file Models
import typing
import logging
from enum import auto
from strenum import StrEnum
from modules.common.TimeUtils import get_timestamp_iso_utc_now

# Logging
logger = logging.getLogger(__name__)


class ManifestDocument:
    """Top-level data model for manifest document"""
    def __init__(self, timestamp: str = None):
        """Constructor for the Manifest file root content

        Keyword Arguments:
            timestamp -- timestampe string (default: {None})
        """
        if timestamp is None:
            timestamp = get_timestamp_iso_utc_now()
        self.session: str = timestamp
        self.created: str = timestamp
        self.modified: str = timestamp
        self.steps: typing.Dict[str, ManifestStep] = dict()
        self.status: str = ManifestStatus.FAILED
        self.status_completion: str = ManifestStatus.NOT_COMPLETED
        self.status_validation: str = ManifestStatus.NOT_VALIDATED
        self.msg_completion: str = ManifestStatus.NOT_SET
        self.msg_validation: str = ManifestStatus.NOT_SET


class ManifestStep:
    """Data model for manifest step"""
    def __init__(self, timestamp: str = None):
        """Constructor for the Manifest file root content

        Keyword Arguments:
            timestamp -- timestampe string (default: {None})
        """
        if timestamp is None:
            timestamp = get_timestamp_iso_utc_now()
        self.created: str = timestamp
        self.modified: str = timestamp
        self.name: str = ManifestStatus.NO_NAME
        self.resources: list = list()
        self.status_completion: str = ManifestStatus.NOT_COMPLETED
        self.status_validation: str = ManifestStatus.NOT_VALIDATED
        self.msg_completion: str = ManifestStatus.NOT_SET
        self.msg_validation: str = ManifestStatus.NOT_SET


class ManifestResource:
    """Data model for manifest resource"""
    def __init__(self, timestamp: str = None):
        """Constructor for the Manifest file root content

        Keyword Arguments:
            timestamp -- timestampe string (default: {None})
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
    """Data model for manifest resource checksums
    """
    def __init__(self):
        self.crc32 = ManifestStatus.NOT_SET
        self.md5sum = ManifestStatus.NOT_SET
        self.sha256sum = ManifestStatus.NOT_SET


class ManifestStatus(StrEnum):
    """Manifest status enums"""
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

# Manifest file Models
import typing
import logging
from enum import StrEnum
from modules.common.TimeUtils import get_timestamp_iso_utc_now

# Logging
logger = logging.getLogger(__name__)

# TODO - Global Data model
class ManifestDocument(object):
    def __init__(self, timestamp :str =None):
        """
        Constructor for the Manifest file root content
        """
        if timestamp is None:
            timestamp = get_timestamp_iso_utc_now()
        self.session :str = timestamp
        self.created :str = timestamp
        self.modified :str = timestamp
        self.steps :typing.Dict[str, ManifestStep] = dict()
        self.status_completion :str = ManifestStatus.UNKNOWN
        self.status_validation :str = ManifestStatus.UNKNOWN
        self.msg_completion :str = ManifestStatus.UNKNOWN
        self.msg_validation :str = ManifestStatus.NOT_VALIDATED

# TODO - Step Data model
class ManifestStep(object):
    def __init__(self, timestamp :str =None):
        if timestamp is None:
            timestamp = get_timestamp_iso_utc_now()
        self.created :str = timestamp
        self.modified :str = timestamp
        self.name :str = ManifestStatus.NO_NAME
        self.resources :list = list()
        self.status_completion :str = ManifestStatus.UNKNOWN
        self.status_validation :str = ManifestStatus.UNKNOWN
        self.msg_completion :str = ManifestStatus.UNKNOWN
        self.msg_validation :str = ManifestStatus.NOT_VALIDATED

# TODO - Resource data model
class ManifestResource(object):
    def __init__(self, timestamp :str =None):
        if timestamp is None:
            timestamp = get_timestamp_iso_utc_now()
        self.created :str = timestamp
        self.modified :str = timestamp
        self.source_url :str = ManifestStatus.NOT_SET
        self.path_destination :str = ManifestStatus.NOT_SET
        self.sha1sum :str = ManifestStatus.NOT_SET
        self.md5sum : str = ManifestStatus.NOT_SET
        self.status_completion :str = ManifestStatus.UNKNOWN
        self.status_validation :str = ManifestStatus.UNKNOWN
        self.msg_completion :str = ManifestStatus.UNKNOWN
        self.msg_validation :str = ManifestStatus.NOT_VALIDATED

class ManifestStatus(StrEnum):
    ERROR = "ERROR"
    FAILED = "FAILED"
    NO_NAME = "NONAME"
    UNKNOWN = "UNKNOWN"
    SUCCESS = "SUCCESS"
    INVALID = "INVALID"
    NOT_SET = "NOT_SET"
    NOT_PROVIDED = "NOT_PROVIDED"
    NOT_VALIDATED = "NOT_VALIDATED"


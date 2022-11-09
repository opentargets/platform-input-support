# Manifest file Models
import typing
import logging
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

# TODO - Step Data model
class ManifestStep:
    def __init__(self):
        timestamp :str = get_timestamp_iso_utc_now()
        self.created :str = timestamp
        self.modified :str = timestamp
        self.step :str = "NONAME"

# TODO - Resource data model
class ManifestResource:
    def __init__(self):
        timestamp :str = get_timestamp_iso_utc_now()
        self.created :str = timestamp
        self.modified :str = timestamp
        self.source_url :str = "NOT SPECIFIED"
        self.path_destination :str = "NOT SPECIFIED"
        self.checksum :str = "NOT SPECIFIED"

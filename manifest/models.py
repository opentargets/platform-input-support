# Manifest file Models
import time
import typing

# TODO - Global Data model
class ManifestDocument:
    def __init__(self):
        """
        Constructor for the Manifest file root content
        """
        timestamp :float = time.time()
        self.created :float = timestamp
        self.modified :float = timestamp
        self.steps :typing.Dict[str, ManifestStep] = dict()

# TODO - Step Data model
class ManifestStep:
    def __init__(self):
        timestamp :float = time.time()
        self.created :float = timestamp
        self.modified :float = timestamp
        self.steps = typing.Dict[str, ManifestResource]

# TODO - Resource data model
class ManifestResource:
    def __init__(self):
        timestamp :float = time.time()
        self.created :float = timestamp
        self.modified :float = timestamp
        self.source_url :str = "NOT SPECIFIED"
        self.path_destination :str = "NOT SPECIFIED"
        self.checksum :str = "NOT SPECIFIED"

"""Task definitions.

This module contains the task and pretask classes.
"""

# these are imported to make them easier access for the implementers
from pis.config.models import PretaskDefinition, TaskDefinition
from pis.manifest.models import Resource
from pis.manifest.task_reporter import TaskManifest, report
from pis.task import Pretask, Task
from pis.validators import v

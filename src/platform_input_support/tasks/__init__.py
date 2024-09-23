"""Task definitions.

This module contains the task and pretask classes.
"""

# these are imported to make them easier access for the implementers
from platform_input_support.config.models import PretaskDefinition, TaskDefinition
from platform_input_support.manifest.models import Resource
from platform_input_support.manifest.task_reporter import TaskManifest, report
from platform_input_support.task import Pretask, Task
from platform_input_support.validators import v

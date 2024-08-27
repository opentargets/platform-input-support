from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Self

from loguru import logger

from platform_input_support.config.models import TaskDefinition
from platform_input_support.manifest.models import Resource
from platform_input_support.manifest.task_reporter import report
from platform_input_support.task import Task
from platform_input_support.validators import v
from platform_input_support.validators.file import file_exists


@dataclass
class HelloWorldDefinition(TaskDefinition):
    who: str = 'world'
    destination: Path = Path('/path/to/output/file.txt')


class HelloWorld(Task):
    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: HelloWorldDefinition

    @report
    def run(self, *, abort: Event) -> Self:
        # configure
        who = self.definition.who

        # write a example string to the destination file
        output_file = Path(self.definition.destination)
        output_file.write_text(f'Hello, {who}!')

        # set the resource
        self.resource = Resource(source='hello_world', destination=str(output_file))

        logger.info(f'completed task hello_world for {who}')
        return self

    @report
    def validate(self, *, abort: Event) -> Self:
        v(file_exists, self.definition.destination)
        return self

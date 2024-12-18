"""Simple hello world task."""

from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Self

from loguru import logger

from pis.tasks import Resource, Task, TaskDefinition, report, v
from pis.validators.file import file_exists


@dataclass
class HelloWorldDefinition(TaskDefinition):
    """Configuration fields for the hello_world task.

    This task has the following custom configuration fields:
        - who (str): The person to greet in the output file.
    """

    who: str = 'world'


class HelloWorld(Task):
    """Simple hello world task."""

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

from dataclasses import dataclass
from threading import Event
from typing import Self

from loguru import logger

from platform_input_support.config.models import TaskDefinition
from platform_input_support.manifest.task_reporter import report
from platform_input_support.task import Task


@dataclass
class HelloWorldDefinition(TaskDefinition):
    who: str = 'world'


class HelloWorld(Task):
    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: HelloWorldDefinition

    @report
    def run(self, *, abort: Event) -> Self:
        who = self.definition.who

        logger.info(f'hello, {who}!')

        logger.success(f'completed task hello_world for {who}')
        return self

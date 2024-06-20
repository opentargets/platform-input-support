from dataclasses import dataclass

from loguru import logger

from platform_input_support.config.models import TaskDefinition
from platform_input_support.manifest import report_to_manifest
from platform_input_support.task import Task


@dataclass
class HelloWorldDefinition(TaskDefinition):
    who: str = 'world'


class HelloWorld(Task):
    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: HelloWorldDefinition

    @report_to_manifest
    def run(self):
        who = self.definition.who

        logger.info(f'hello, {who}!')

        return f'completed task hello_world for `{who}`'

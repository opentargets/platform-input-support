from dataclasses import dataclass

from loguru import logger

from platform_input_support.manifest import report_to_manifest
from platform_input_support.task import Task, TaskConfigMapping


@dataclass
class HelloWorldConfigMapping(TaskConfigMapping):
    who: str = 'world'


class HelloWorld(Task):
    def __init__(self, config: TaskConfigMapping):
        self.config: HelloWorldConfigMapping
        super().__init__(config)

    @report_to_manifest
    def run(self):
        logger.info(f'hello, {self.config.who}!')

        return f'completed task hello_world for {self.config.who}'

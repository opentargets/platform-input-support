from dataclasses import dataclass

from loguru import logger

from . import Task, TaskMapping, report_to_manifest


@dataclass
class HelloWorldMapping(TaskMapping):
    who: str = 'world'


class HelloWorld(Task):
    def __init__(self, config: TaskMapping):
        super().__init__(config)
        self.config: HelloWorldMapping

    @report_to_manifest
    def run(self):
        logger.info(f'hello, {self.config.who}!')

        return f'completed task hello_world for {self.config.who}'

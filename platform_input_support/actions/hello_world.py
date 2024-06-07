from dataclasses import dataclass
from typing import Any

from loguru import logger

from platform_input_support.action.action import Action, ActionConfigMapping
from platform_input_support.manifest.manifest import report_to_manifest


@dataclass
class HelloWorldConfigMapping(ActionConfigMapping):
    who: str = 'world'


class HelloWorld(Action):
    def __init__(self, config: dict[str, Any]):
        self.config: HelloWorldConfigMapping
        super().__init__(config)

    @report_to_manifest
    def run(self):
        logger.info(f'Hello, {self.config.who}!')

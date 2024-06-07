from dataclasses import dataclass
from typing import Any

from loguru import logger

from platform_input_support.action.action import Action, ActionConfigMapping


@dataclass
class HelloWorldConfigMapping(ActionConfigMapping):
    name: str = 'world'


class HelloWorld(Action):
    def __init__(self, config: dict[str, Any]):
        self.config: HelloWorldConfigMapping
        super().__init__(config)

    def run(self):
        self.start_action()

        try:
            logger.info(f'Hello, {self.config.name}!')
        except Exception as e:
            self.fail_action(f'error: {e}')
            return

        self.complete_action()

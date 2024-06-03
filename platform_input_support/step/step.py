from loguru import logger

from platform_input_support.config import config
from platform_input_support.manifest import StepReporter


class Step(StepReporter):
    def __init__(self):
        self.name = self.__class__.__name__.lower()
        self.parts = config.steps[self.name]

        super().__init__()

        logger.debug(f'initialized step {self.name}')

    def run(self):
        pass

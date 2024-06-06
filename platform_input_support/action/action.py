from loguru import logger

from platform_input_support.config.models import ActionMapping
from platform_input_support.manifest.manifest import ActionReporter


class Action(ActionReporter):
    def __init__(self, config: ActionMapping):
        self.name = self.__class__.__name__.lower()
        self.config = config

        super().__init__()

        logger.debug(f'initialized action {self.name}')

    def run(self):
        pass

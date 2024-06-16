from loguru import logger

from platform_input_support.config.models import TaskMapping
from platform_input_support.manifest import TaskReporter
from platform_input_support.scratch_pad import scratch_pad


class Task(TaskReporter):
    def __init__(self, config: TaskMapping):
        super().__init__(config.name)
        self.config = config

        # replace templates in the config strings
        for key, value in vars(self.config).items():
            if isinstance(value, str):
                setattr(self.config, key, scratch_pad.replace(value))

        logger.debug(f'initialized task {self.name}')

    def run(self) -> str | None:
        pass

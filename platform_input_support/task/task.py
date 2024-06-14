import sys
from dataclasses import dataclass
from importlib import import_module
from typing import Any

from loguru import logger

from platform_input_support.manifest.manifest import TaskReporter
from platform_input_support.scratch_pad import scratch_pad


@dataclass
class TaskConfigMapping:
    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(**data)


class Task(TaskReporter):
    def __init__(self, config: TaskConfigMapping | dict[str, Any]):
        task_class = self.__class__.__name__
        self.name = task_class

        # instantiate a configuration subclass coming from this task module
        if isinstance(config, dict):
            task_module = import_module(self.__module__)
            config_class = f'{task_class}ConfigMapping'
            config_instance: TaskConfigMapping = getattr(task_module, config_class)

            try:
                self.config = config_instance.from_dict(config)
            except TypeError as e:
                logger.critical(f'invalid config for {task_class}: {e}')
                sys.exit(1)

        # replace templates in the config strings
        for key, value in vars(self.config).items():
            if isinstance(value, str):
                setattr(self.config, key, scratch_pad.replace(value))

        super().__init__(self.name)

        logger.debug(f'initialized task {self.name}')

    def run(self) -> str | None:
        pass

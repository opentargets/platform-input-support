import sys
from importlib import import_module
from typing import Any

from attr import dataclass
from loguru import logger

from platform_input_support.manifest.manifest import ActionReporter
from platform_input_support.scratch_pad import scratch_pad


@dataclass
class ActionConfigMapping:
    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(**data)


class Action(ActionReporter):
    def __init__(self, config: ActionConfigMapping | dict[str, Any]):
        action_class = self.__class__.__name__
        self.name = action_class

        # instantiate a configuration subclass coming from this action module
        if isinstance(config, dict):
            action_module = import_module(self.__module__)
            config_class = f'{action_class}ConfigMapping'
            config_instance: ActionConfigMapping = getattr(action_module, config_class)

            try:
                self.config = config_instance.from_dict(config)
            except TypeError as e:
                logger.critical(f'invalid config for {action_class}: {e}')
                sys.exit(1)

        # replace templates in the config strings
        for key, value in vars(self.config).items():
            if isinstance(value, str):
                setattr(self.config, key, scratch_pad.replace(value))

        super().__init__(self.name)

        logger.debug(f'initialized action {self.name}')

    def run(self) -> str | None:
        pass

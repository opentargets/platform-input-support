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
    def __init__(self, config: dict[str, Any]):
        action_class = self.__class__.__name__
        self.name = action_class.lower()

        # replace templates in the config strings
        for key, value in config.items():
            if isinstance(value, str):
                config[key] = scratch_pad.replace(value)

        action_module = import_module(self.__module__)
        config_class = f'{action_class}ConfigMapping'
        config_mapping: ActionConfigMapping = getattr(action_module, config_class)

        try:
            self.config = config_mapping.from_dict(config)
        except TypeError as e:
            logger.critical(f'invalid config for {action_class}: {e}')
            sys.exit(1)

        super().__init__()

        logger.debug(f'initialized action {self.name}')

    def run(self) -> str | None:
        pass

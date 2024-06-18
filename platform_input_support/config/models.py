import inspect
from dataclasses import dataclass
from typing import Any, TypeVar

from loguru import logger

_T = TypeVar('_T', bound='TaskMapping')


@dataclass
class TaskMapping:
    name: str
    config_dict: dict[str, Any]

    @classmethod
    def from_dict(cls: type[_T], config_dict: dict) -> _T:
        name: str = ''
        try:
            name = config_dict['name']
        except KeyError:
            logger.critical('missing field name in a task definition, check configuration file')
        return cls(name=name, config_dict=config_dict)

    def real_name(self):
        return self.name.split(' ')[0]


@dataclass
class ConfigMapping:
    step: str
    output_path: str = './output'
    gcs_url: str | None = None
    force: bool = False
    log_level: str = 'INFO'

    @classmethod
    def from_dict(cls, data: dict):
        kwargs = {}
        for param in inspect.signature(cls).parameters:
            kwargs[param] = data.get(param)
        return cls(**kwargs)

    def __add__(self, other):
        # merge the settings from two objects keeping the values from the other object
        for key, value in other.__dict__.items():
            if value is not None or getattr(self, key) is None:
                setattr(self, key, value)

        return self


@dataclass
class RootMapping:
    config: ConfigMapping
    scratchpad: dict[str, str]
    steps: dict[str, list[TaskMapping]]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            config=ConfigMapping.from_dict(data['config']),
            scratchpad=data['scratchpad'],
            steps={step: [TaskMapping.from_dict(task) for task in tasks] for step, tasks in data['steps'].items()},
        )

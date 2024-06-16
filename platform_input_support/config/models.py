import inspect
from dataclasses import dataclass
from typing import Any


@dataclass
class TaskMapping:
    name: str
    config: dict[str, Any]  # this becomes a TaskConfigMapping once the task is instantiated

    @classmethod
    def from_dict(cls, data: dict):
        name = data.pop('name')
        return cls(name=name, config=data)

    def real_name(self):
        return self.name.split(' ')[0]


@dataclass
class ConfigMapping:
    step: str
    output_path: str = './output'
    gcs_url: str | None = None
    log_level: str = 'INFO'

    @classmethod
    def from_dict(cls, data: dict):
        kwargs = {}

        # make sure it fills all the class arguments, but no more
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
    scratch_pad: dict[str, str]
    steps: dict[str, list[TaskMapping]]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            config=ConfigMapping.from_dict(data['config']),
            scratch_pad=data['scratch_pad'],
            steps={step: [TaskMapping.from_dict(task) for task in tasks] for step, tasks in data['steps'].items()},
        )

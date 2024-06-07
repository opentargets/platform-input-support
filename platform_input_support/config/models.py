import inspect
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ActionMapping:
    name: str
    config: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict):
        name = data.pop('name')
        return cls(name=name, config=data)


@dataclass
class StepMapping:
    actions: list[ActionMapping]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(actions=[ActionMapping.from_dict(action) for action in data])


@dataclass
class ConfigMapping:
    step: str
    output_path: str = './output'
    gcp_credentials_path: str | None = None
    gcp_bucket_path: str | None = None
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
    steps: dict[str, StepMapping]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            config=ConfigMapping.from_dict(data['config']),
            steps={step: StepMapping.from_dict(step_data) for step, step_data in data['steps'].items()},
        )

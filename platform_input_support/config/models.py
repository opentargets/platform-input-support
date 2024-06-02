import inspect
from dataclasses import dataclass, field


@dataclass
class ActionSettings:
    pass


class ParseConfigError:
    pass


@dataclass
class ActionModel:
    name: str
    config: dict[str, ActionSettings]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(name=data['name'], config=data['config'])


@dataclass
class StepModel:
    actions: list[ActionModel]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(actions=[ActionModel.from_dict(action) for action in data['actions']])


@dataclass
class SettingsModel:
    output_path: str = './output'
    gcp_credentials_path: str | None = None
    gcp_bucket_path: str | None = None
    include: set[str] = field(default_factory=set)
    exclude: set[str] = field(default_factory=set)
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
class ConfigModel:
    settings: SettingsModel
    steps: dict[str, StepModel]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            settings=SettingsModel.from_dict(data['settings']),
            steps={step: StepModel.from_dict(step_data) for step, step_data in data['steps'].items()},
        )

from pathlib import Path
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel

LOG_LEVELS = Literal['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']


def gcs_url_is_valid(url: str) -> str:
    assert url.startswith('gs://'), 'GCS url must start with gs://'
    return url


class TaskDefinition(BaseModel, extra='allow'):
    """Task definition model.

    This model is used to define a task in a step. It is extended in subclasses
    to add the task-specific attributes.

    Attributes:
        name (str): The name of the task.
    """

    name: str


class MainTaskDefinition(TaskDefinition, BaseModel, extra='allow'):
    destination: Path


class EnvSettings(BaseModel):
    step: str | None = None
    config_file: Path | None = None
    work_dir: Path | None = None
    gcs_url: Annotated[str, AfterValidator(gcs_url_is_valid)] | None = None
    force: bool | None = None
    log_level: LOG_LEVELS | None = None


class CliSettings(BaseModel):
    step: str = ''
    config_file: Path | None = None
    work_dir: Path | None = None
    gcs_url: Annotated[str, AfterValidator(gcs_url_is_valid)] | None = None
    force: bool | None = None
    log_level: LOG_LEVELS | None = None


class YamlSettings(BaseModel):
    work_dir: Path | None = None
    gcs_url: Annotated[str, AfterValidator(gcs_url_is_valid)] | None = None
    force: bool | None = None
    log_level: LOG_LEVELS | None = None


class Settings(BaseModel):
    """Settings model.

    This model is used to define the settings for the application. It is
    constructed by merging the settings from the environment, CLI, and YAML
    configuration file. The fields are defined in the order of precedence, with
    the environment settings taking precedence over the CLI settings, which
    take precedence over the YAML settings. All fields have defaults so that
    any field left unset after the merge will have a value. The `step` and
    `gcs_url` fields are required, but have an empty string as a default value,
    so objects can be created without setting these fields. Their validation is
    handled by the CLI/Google helper.


    Attributes:
        step (str): The step to run.
        config_file (Path): The path to the configuration file.
        work_dir (Path): The local working directory path.
        gcs_url (str): The Google Cloud Storage URL.
        force (bool): Whether to force the operation.
        log_level (str): The log level.
    """

    step: str = ''  # validation of this field is handled by cli.py
    config_file: Path = Path('config.yaml')
    work_dir: Path = Path('./output')
    gcs_url: Annotated[str, AfterValidator(gcs_url_is_valid)] = ''
    force: bool = False
    log_level: LOG_LEVELS = 'INFO'

    def merge_model(self, incoming: BaseModel):
        for field_name in self.model_fields:
            if field_name in incoming.model_fields_set:
                field_value = getattr(incoming, field_name)
                setattr(self, field_name, field_value)

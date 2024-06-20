from pathlib import Path
from typing import Annotated, Literal
from xmlrpc.client import Boolean

from pydantic import AfterValidator, BaseModel, ConfigDict

LOG_LEVELS = Literal['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']


def gcs_url_is_valid(url: str) -> str:
    assert url.startswith('gs://'), 'GCS url must start with gs://'
    return url


class TaskDefinition(BaseModel):
    name: str
    model_config = ConfigDict(extra='allow')


class EnvVarSettings(BaseModel):
    step: str | None = None
    config_file: Path | None = None
    work_dir: Path | None = None
    gcs_url: Annotated[str, AfterValidator(gcs_url_is_valid)] | None = None
    force: Boolean | None = None
    log_level: LOG_LEVELS | None = None


class CliSettings(BaseModel):
    step: str
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
    step: str = ''  # validation of this field is handled by cli.py
    config_file: Path = Path('config.yaml')
    work_dir: Path = Path('./output')
    gcs_url: Annotated[str, AfterValidator(gcs_url_is_valid)] | None = None
    force: bool = False
    log_level: LOG_LEVELS = 'INFO'

    def merge_model(self, incoming: BaseModel):
        for field_name in self.model_fields:
            if field_name in incoming.model_fields_set:
                field_value = getattr(incoming, field_name)
                setattr(self, field_name, field_value)

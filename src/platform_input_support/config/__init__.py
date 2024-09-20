from typing import TYPE_CHECKING

from platform_input_support.config.scratchpad import Scratchpad

if TYPE_CHECKING:
    from platform_input_support.config.config import Config
    from platform_input_support.config.models import BaseTaskDefinition

_config: 'Config | None' = None
_steps: 'list[str] | None' = None
_task_definitions: 'list[BaseTaskDefinition] | None' = None
_scratchpad: 'Scratchpad | None' = None


def init_config():
    global _config  # noqa: PLW0603
    if _config is None:
        from platform_input_support.config.config import Config

        _config = Config()


def settings():
    """Return the application settings.

    Attributes:
        step (str): The step to run.
        config_file (Path): The path to the configuration file.
        work_dir (Path): The local working directory path.
        gcs_url (str): The Google Cloud Storage URL.
        pool (int): The number of workers in the pool.
        log_level (str): The log level.

    Returns:
        Settings: The settings object.
    """
    if _config is None:
        init_config()
    assert _config is not None
    return _config.settings


def steps():
    """Return the steps.

    If the steps have not been loaded, they will be loaded from the configuration
    file. The steps are stored for subsequent calls.

    Returns:
        list[str]: The steps.
    """
    global _config, _steps  # noqa: PLW0602, PLW0603
    init_config()
    assert _config is not None
    if _steps is None:
        _steps = _config.yaml_dict['steps']
    return _steps or []


def task_definitions():
    """Return the task definitions.

    If the task definitions have not been loaded, they will be loaded from the
    configuration file. The task definitions are stored for subsequent calls.

    Returns:
        list[TaskDefinitions]: The task definitions.
    """
    global _config, _task_definitions  # noqa: PLW0602, PLW0603
    init_config()
    assert _config is not None
    if _task_definitions is None:
        _task_definitions = _config.get_task_definitions()
    return _task_definitions


def scratchpad():
    """Return the scratchpad.

    If the scratchpad has not been initialized, it will be initialized. The
    scratchpad is stored for subsequent calls.

    Returns:
        Scratchpad: The scratchpad.
    """
    global _config, _scratchpad  # noqa: PLW0602, PLW0603
    init_config()
    assert _config is not None
    if _scratchpad is None:
        _scratchpad = Scratchpad(_config.get_scratchpad_sentinel_dict())
    return _scratchpad

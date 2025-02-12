"""Task classes for PIS."""

from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Self

from loguru import logger

from pis.config import scratchpad, settings
from pis.config.models import BaseTaskDefinition, TaskDefinition
from pis.manifest.task_reporter import TaskReporter, report
from pis.storage.remote_storage import get_remote_storage
from pis.util.fs import absolute_path

if TYPE_CHECKING:
    from pis.manifest.models import Resource


class Task(TaskReporter):
    """Base class for all tasks.

    Tasks are the main building blocks of PIS. They are responsible for running the
    various operations that are needed to gather the data from the different sources.

    Tasks are defined by a TaskDefinition object, which contains the configuration
    fields for the task. The Task class only needs to implement how it runs and validates
    itself. All the initialization, registration and reporting is handled internally
    by parent classes and PIS itself.

    To implement a new task, create a new TaskDefinition class that inherits from
    TaskDefinition or and contains the configuration fields required. Then, create a
    new class that inherits from Task and implements the run and the validate methods.

    The name of the class, converted to snake_case, will be the real name of the task,
    which is used to identify the task in the registry and in the configuration file.

    For example, for a DoSomething task, the real name will be do_something, and
    in the configuration file, it could be used inside a step like this:

    .. code-block:: yaml

        steps:
            - do_something to create an example resource:
                some_field: some_value
                another_field: another_value

    :param definition: The definition of the task.
    :type definition: BaseTaskDefinition
    :ivar definition: The definition of the task.
    :vartype definition: BaseTaskDefinition
    :ivar resource: The resource object associated with the task.
    :vartype resource: Resource
    """

    def __init__(self, definition: BaseTaskDefinition):
        super().__init__(definition.name)
        self.definition = definition
        self.resource: Resource

        # replace templates in the definition strings
        for key, value in self.definition.model_dump().items():
            if isinstance(value, str | Path):
                setattr(self.definition, key, scratchpad().replace(value))

        logger.debug(f'initialized task {self.name}')

    @report
    def run(self, *, abort: Event) -> Self:
        """Run the task.

        This method contains the actual work of the task. All tasks must implement
        `run`, and it must download or generate a resource in the path stored in the
        destination field of the task definition.

        Optionally, an `abort` event can be watched to stop the task if another task
        has failed. This is useful for long running work that can be stopped midway
        once the run is deemed to be a failure.

        :param abort: The event that will be set if another task has failed.
        :type abort: Event
        :return: The task instance itself must be returned.
        :rtype: Self
        """
        return self

    @report
    def validate(self, *, abort: Event) -> Self:
        """Validate the task.

        This method should be implemented by the task subclass to perform validation. If
        not implemented, the task resource will always be considered valid.

        The validate method should make use of the `v` method from the validators module
        to invoke a series of validators. See :func:`pis.validators.v`.

        :param abort: The event that will be set if another task has failed.
        :type abort: Event
        :return: The task instance itself must be returned.
        :rtype: Self
        """
        return self

    @report
    def upload(self, *, abort: Event) -> Self:
        """Upload the task.

        This method will upload the file generated by the task to the remote uri. The
        destination field of the task definition will be used as the path in the bucket.

        There is no need to implement this method in the subclass unless the task needs
        some special handling for the upload, which is unlikely.

        :param abort: The event that will be set if another task has failed.
        :type abort: Event
        :return: The task instance itself must be returned.
        :rtype: Self
        """
        assert isinstance(self.definition, TaskDefinition)

        source = absolute_path(self.definition.destination)
        remote_uri = settings().remote_uri
        assert remote_uri is not None
        destination = f'{remote_uri}/{self.definition.destination!s}'
        remote_storage = get_remote_storage(remote_uri)
        remote_storage.upload(source, destination)
        return self


class Pretask(Task):
    """Base class for all pretasks.

    Pretasks are tasks that are run before the main tasks. They are used to prepare the
    environment for the main tasks. For example: getting a list of files to later download
    one or all of them; or generating a new set of tasks based on some parameters.

    Pretasks are defined by a PretaskDefinition object, which contains the configuration
    fields for the pretask. The Pretask class only needs to implement `run`. All the
    initialization, registration and reporting is handled internally by parent classes
    and PIS itself.

    To implement a new pretask, create a new PretaskDefinition class that inherits from
    TaskDefinition or and contains the configuration fields required. Then, create a
    new class that inherits from Pretask and implements the run method.

    The name of the class, converted to snake_case, will be the 'real name' of the pretask,
    which is used to identify the pretask in the registry and in the configuration file.
    """

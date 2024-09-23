"""Pretask — explode tasks based on a list of dictionaries."""

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from threading import Event
from typing import Any, Self, cast

import jq
from loguru import logger

from platform_input_support.config import scratchpad, task_definitions
from platform_input_support.helpers.download import download
from platform_input_support.tasks import Pretask, PretaskDefinition, TaskDefinition, report
from platform_input_support.util.misc import list_str


@dataclass
class ExplodeDefinition(PretaskDefinition):
    """Configuration fields for the explode pretask.

    This pretask has the following custom configuration fields:
        - do (list[dict]): The tasks to explode. Each task in the list will be
            duplicated for each iteration of the foreach list.
        - foreach (list[dict[str, str]] | None): The list of dictionaries to iterate
            over. Each item in the list will be used to replace the variables in the
            tasks in the do list.
        - foreach_function (str | None): If set, this function will be called to get
            the foreach list. The function must return a list of dictionaries.
        - foreach_function_args (dict[str, Any] | None): Arguments to pass to the
            foreach function.
    """

    do: list[dict]
    foreach: list[dict[str, str]] | None = None
    foreach_function: str | None = None
    foreach_function_args: dict[str, Any] | None = None


class Explode(Pretask):
    """Explode tasks based on a list of dictionaries.

    This pretask will duplicate the tasks in the `do` list for each iteration of the
    `foreach` list. The `foreach` list is a list of dictionaries where each dictionary
    will be used to replace the variables in the tasks in the `do` list.

    If the `foreach` list is not set, the `foreach_function` will be called to get the
    list of dictionaries. The function must return a list of dictionaries.
    """

    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: ExplodeDefinition

    @report
    def run(self, *, abort: Event) -> Self:
        do = self.definition.do
        foreach = self.definition.foreach
        foreach_function = self.definition.foreach_function
        foreach_function_args = self.definition.foreach_function_args or {}

        if foreach is None and foreach_function is None:
            logger.critical('either foreach or foreach_function must be set')
            sys.exit(1)

        description = self.name.split(' ', 1)[1] if ' ' in self.name else ''
        logger.debug(f'exploding {description}')

        # if foreach_function is set, call the function and use its return value as the foreach list
        if foreach_function:
            func_obj = globals().get(foreach_function)
            if not func_obj:
                logger.critical(f'function {foreach_function} not found')
                sys.exit(1)

            func = cast(Callable[..., list[dict[str, str]]], func_obj)
            args_str = list_str(foreach_function_args, dict_values=True)
            logger.debug(f'calling function {foreach_function} with args {args_str}')
            foreach = func(**foreach_function_args)

        foreach = foreach or []
        logger.debug(f'exploding {len(do)} tasks by {len(foreach)} iterations')
        new_tasks = 0

        for d in foreach:
            for k1, v1 in d.items():
                scratchpad().store(k1, v1)

            for task in do:
                task_definition = {k2: scratchpad().replace(v2) for k2, v2 in task.items()}
                t = TaskDefinition.model_validate(task_definition)
                task_definitions().append(t)
                new_tasks += 1

        logger.info(f'exploded into {new_tasks} new tasks')
        return self


def urls_from_json(
    source: str,
    destination: str,
    json_path: str,
    prefix: str | None,
) -> list[dict[str, str]]:
    """Get a list of URLs from a JSON file.

    This function will download a JSON file from a URL, extract a list of URLs from it
    using a JQ query, and return a list of dictionaries with the source and destination
    URLs.

    :param source: The URL of the JSON file to download.
    :type source: str
    :param destination: The destination file to save the JSON file to.
    :type destination: str
    :param json_path: The JQ query to extract the URLs from the JSON file.
    :type json_path: str
    :param prefix: If set, this prefix will be removed from the source URLs to generate
        the destination file names.
    :type prefix: str | None

    :return: A list of dictionaries with the source and destination URLs.
    :rtype: list[dict[str, str]]
    """
    destination_file = download(source, destination)
    file_content = destination_file.read_text()
    json_data = json.loads(file_content)
    srcs = jq.compile(json_path).input_value(json_data).all()

    if prefix:
        dsts = [source.replace(prefix, '') for source in srcs]
    else:
        dsts = [source.split('/')[-1] for source in srcs]

    return [{'source': s, 'destination': d} for s, d in zip(srcs, dsts, strict=True)]

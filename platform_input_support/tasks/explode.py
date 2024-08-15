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
    do: list[dict]
    foreach: list[dict[str, str]] | None = None
    foreach_function: str | None = None
    foreach_function_args: dict[str, Any] | None = None


class Explode(Pretask):
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

        logger.success(f'exploded into {new_tasks} new tasks')
        return self


def urls_from_json(
    source: str,
    destination: str,
    json_path: str,
    prefix: str | None,
) -> list[dict[str, str]]:
    """Get download tasks from a JSON file.

    Args:
        source (str): URL to the JSON file to download
        destination (str): Destination path for the JSON file
        json_path (str): jq path to the URLs to retrieve from the file
        prefix (str | None): If present, this prefix will be removed from the URLs
            to generate the destination path where the file will be saved. This is
            useful in case there are multiple URLs in the JSON file with the same
            file name that would end up overwriting each other.
            If this is None, the file name will be used as the destination path.
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

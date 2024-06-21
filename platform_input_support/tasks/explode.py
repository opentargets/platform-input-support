import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

import jq
from loguru import logger

from platform_input_support.config import scratchpad, task_definitions
from platform_input_support.config.models import TaskDefinition
from platform_input_support.helpers.download import download
from platform_input_support.manifest import report_to_manifest
from platform_input_support.task import PreTask
from platform_input_support.util.misc import list_str


@dataclass
class ExplodeDefinition(TaskDefinition):
    do: list[dict]
    foreach: list[dict[str, str]] | None = None
    foreach_function: str | None = None
    foreach_function_args: dict[str, Any] | None = None


class Explode(PreTask):
    def __init__(self, definition: TaskDefinition):
        super().__init__(definition)
        self.definition: ExplodeDefinition

    @report_to_manifest
    def run(self):
        do = self.definition.do
        foreach = self.definition.foreach
        foreach_function = self.definition.foreach_function
        foreach_function_args = self.definition.foreach_function_args or {}

        if foreach is None and foreach_function is None:
            logger.critical('either foreach or foreach_function must be set')
            sys.exit(1)

        description = self.name.split(' ', 1)[1] if ' ' in self.name else ''
        logger.info(f'exploding `{description}`')

        # if foreach_function is set, call the function and use its return value as the foreach list
        if foreach_function:
            func_obj = globals().get(foreach_function)
            if not func_obj:
                logger.critical(f'function `{foreach_function}` not found')
                sys.exit(1)

            func = cast(Callable[..., list[dict[str, str]]], func_obj)
            args_str = list_str(foreach_function_args, dict_values=True)
            logger.info(f'calling function `{foreach_function}` with args `{args_str}`')
            foreach = func(**foreach_function_args)

        foreach = foreach or []
        logger.info(f'exploding {len(do)} tasks by {len(foreach)} iterations')
        new_tasks = 0

        for d in foreach:
            for k1, v1 in d.items():
                scratchpad.store(k1, v1)

            for task in do:
                task_definition = {k2: scratchpad.replace(v2) for k2, v2 in task.items()}
                t = TaskDefinition.model_validate(task_definition)
                task_definitions.append(t)
                new_tasks += 1

        return f'exploded into {new_tasks} new tasks'


def urls_from_json(source: str, destination: str, json_path: str) -> list[dict[str, str]]:
    destination_file = download(source, destination)
    file_content = destination_file.read_text()
    json_data = json.loads(file_content)
    sources = jq.compile(json_path).input_value(json_data).all()

    return [{'source': source, 'destination': source.split('/')[-1]} for source in sources]

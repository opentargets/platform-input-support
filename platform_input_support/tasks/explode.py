import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

import jq
from loguru import logger

from platform_input_support.config import tasks
from platform_input_support.config.models import TaskMapping
from platform_input_support.helpers.download import DownloadHelper
from platform_input_support.manifest import report_to_manifest
from platform_input_support.scratch_pad import scratch_pad
from platform_input_support.task import Task


@dataclass
class ExplodeMapping(TaskMapping):
    do: list[dict]
    foreach: list[dict[str, str]] | None = None
    foreach_function: str | None = None
    foreach_function_args: dict[str, Any] | None = None


class Explode(Task):
    def __init__(self, config: TaskMapping):
        self.config: ExplodeMapping
        super().__init__(config)

    @report_to_manifest
    def run(self):
        if self.config.foreach is None and self.config.foreach_function is None:
            logger.critical('either foreach or foreach_function must be set')
            sys.exit(1)

        description = self.name.split(' ', 1)[1] if ' ' in self.name else ''
        logger.info(f'exploding {description}')

        foreach = self.config.foreach or [{}]

        # if foreach_function is set, call the function and use its return value as the foreach list
        if self.config.foreach_function:
            func_name = self.config.foreach_function
            func_obj = globals().get(func_name)
            if not func_obj:
                logger.critical(f'function {func_name} not found')
                sys.exit(1)

            func = cast(Callable[..., list[dict[str, str]]], func_obj)
            args = self.config.foreach_function_args or {}
            logger.info(f'calling function {func_name} with args {args}')

            try:
                foreach = func(**args)
            except Exception as e:
                self.fail_task(Exception(f'error running foreach function {func_name}: {e}'))

        logger.info(f'exploding {len(self.config.do)} tasks by {len(foreach)} iterations')
        new_tasks = 0

        for d in foreach:
            for k1, v1 in d.items():
                scratch_pad.store(k1, v1)

            for task in self.config.do:
                task_config_dict = {k2: scratch_pad.replace(v2) for k2, v2 in task.items()}
                t = TaskMapping.from_dict(task_config_dict)
                tasks.append(t)
                new_tasks += 1

        return f'exploded into {new_tasks} new tasks'


def urls_from_json(url: str, json_path: str) -> list[dict[str, str]]:
    d = DownloadHelper(url)
    json = d.download_json()
    urls = jq.compile(json_path).input_value(json).all()

    return [{'source': url, 'destination': url.split('/')[-1]} for url in urls]

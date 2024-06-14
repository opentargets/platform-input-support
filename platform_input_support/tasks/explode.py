from dataclasses import dataclass

from loguru import logger

from platform_input_support.config import tasks
from platform_input_support.config.models import TaskMapping
from platform_input_support.manifest import report_to_manifest
from platform_input_support.scratch_pad import scratch_pad
from platform_input_support.task import Task, TaskConfigMapping


@dataclass
class ExplodeConfigMapping(TaskConfigMapping):
    do: list[dict]
    foreach: list[str] | None = None
    foreach_function: str | None = None
    foreach_args: list[str] = None


class Explode(Task):
    def __init__(self, config: TaskConfigMapping):
        self.config: ExplodeConfigMapping
        super().__init__(config)

    @report_to_manifest
    def run(self):
        description = self.name.split(' ', 1)[1] if ' ' in self.name else ''
        logger.info(f'exploding {description}')

        foreach = self.config.foreach
        if foreach is None:
            foreach = self.config.foreach_function(*self.config.foreach_args)

        logger.info(f'exploding {len(self.config.do)} tasks by {len(foreach)} iterations')
        new_tasks = 0
        for item in foreach:
            scratch_pad.store('i', item)
            for task in self.config.do:
                task_config_dict = {k: scratch_pad.replace(v) for k, v in task.items()}
                t = TaskMapping(task_config_dict.pop('name'), task_config_dict)
                tasks.append(t)
                new_tasks += 1

        return f'exploded into {new_tasks} new tasks'

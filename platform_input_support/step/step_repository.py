import sys
from importlib import import_module
from inspect import getmembers, isclass
from pathlib import Path

from loguru import logger

from platform_input_support.config import config
from platform_input_support.step.step import Step


class StepRepository:
    def __init__(self):
        self.steps: dict[str, Step] = {}

    @staticmethod
    def _filename_to_class(filename: str) -> str:
        return filename.replace('_', ' ').title().replace(' ', '').lower()

    def _register_step(self, step_name: str, step: Step):
        self.steps[step_name] = step
        logger.debug(f'registered step {step_name}')

    def register_steps(self):
        steps_dir = Path(__file__).parent.parent / 'steps'
        logger.debug(f'registering steps from {steps_dir}')

        for file_path in steps_dir.glob('*.py'):
            filename = file_path.stem
            step_module = import_module(f'platform_input_support.steps.{filename}')

            if step_module.__spec__ is None:
                continue

            for name, obj in getmembers(step_module):
                name = name.lower()
                if isclass(obj) and name == self._filename_to_class(filename):
                    self._register_step(name, obj())
                    break

    def _get_steps_to_run(self):
        steps = set(config.steps.keys())

        if config.settings.exclude is not None:
            steps -= config.settings.exclude

        if config.settings.include is not None:
            steps = config.settings.include

        for step in steps:
            if step not in self.steps:
                where_is_it = 'configuration file' if step in config.steps else 'command line arguments'
                logger.critical(f'step {step} defined in {where_is_it} is not in the step repository')
                sys.exit(1)

        return list(steps)

    def run(self):
        steps_to_run = self._get_steps_to_run()

        logger.info(f'starting run with steps {steps_to_run}')

        step_name: str
        for step_name in steps_to_run:
            logger.info(f'running step {step_name}')
            self.steps[step_name].run()

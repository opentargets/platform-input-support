from multiprocessing import Pool

from loguru import logger

from platform_input_support.action import action_repository
from platform_input_support.config.models import ActionMapping, StepMapping
from platform_input_support.manifest.manifest import StepReporter

PARALLEL_STEP_COUNT = 5
PREPROCESS_ACTIONS = ['explode', 'get_file_list']


class Step(StepReporter):
    def __init__(self, name: str, step_mapping: StepMapping):
        self.name: str = name
        self.actions: list[ActionMapping] = step_mapping.actions

        super().__init__(name)

    def _preprocess(self):
        for i, action_mapping in enumerate(self.actions):
            if action_mapping.get_action_effective_name() in PREPROCESS_ACTIONS:
                self._run_action(action_mapping)
                del self.actions[i]

    def _run_action(self, action_mapping: ActionMapping):
        action_type = action_repository.actions[action_mapping.get_action_effective_name()]
        action = action_type(action_mapping)
        self.add_action(action._report)

        with logger.contextualize(action=action.name):
            try:
                action.run()
            except Exception as e:
                self.fail_step(e)

    def run(self):
        self.start_step()

        logger.info('running preprocessing actions')
        self._preprocess()

        logger.info('running main actions')
        with Pool(PARALLEL_STEP_COUNT) as p:
            p.map(self._run_action, self.actions)

        self.complete_step()

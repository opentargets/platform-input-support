from multiprocessing.pool import Pool

from loguru import logger

from platform_input_support.action import action_repository
from platform_input_support.config.models import ActionMapping, StepMapping
from platform_input_support.manifest.manifest import StepReporter

PARALLEL_STEP_COUNT = 5
PREPROCESS_ACTIONS = ['explode', 'get_file_list']


class Step(StepReporter):
    def __init__(self, name: str, step_mapping: StepMapping):
        self.name: str = name
        self.action_mappings = step_mapping.actions
        super().__init__(name)

    def _get_preprocess_actions(self) -> list[ActionMapping]:
        return [
            self.action_mappings.pop(i)
            for i, j in enumerate(self.action_mappings)
            if j.real_name() in PREPROCESS_ACTIONS
        ]

    def _run_action(self, am: ActionMapping):
        action_type = action_repository.actions[am.real_name()]
        action = action_type(am.config)
        action.name = am.name

        with logger.contextualize(action=action.name):
            try:
                action.run()
            except Exception as e:
                self.fail_step(e)

    def run(self):
        self.start_step()

        preprocess_actions = self._get_preprocess_actions()
        logger.info(f'Running {len(preprocess_actions)} preprocess actions')
        for am in preprocess_actions:
            self._run_action(am)

        logger.info(f'Running {len(self.action_mappings)} main actions')
        pool = Pool(PARALLEL_STEP_COUNT)
        pool.map(self._run_action, self.action_mappings)

        self.complete_step()

from platform_input_support.action import action_repository
from platform_input_support.config.models import ActionMapping, StepMapping
from platform_input_support.manifest.manifest import StepReporter


class Step(StepReporter):
    def __init__(self, name: str, step_mapping: StepMapping):
        self.name: str = name
        self.actions: list[ActionMapping] = step_mapping.actions

        super().__init__(name)

    def run(self):
        self.start_step()

        for action_mapping in self.actions:
            action = action_repository.actions[action_mapping.name](action_mapping.config)
            self.add_action(action._report)

            try:
                action.run()
            except Exception as e:
                self.fail_step(e)

        self.complete_step()

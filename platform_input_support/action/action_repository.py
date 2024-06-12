from importlib import import_module
from inspect import getmembers, isclass
from pathlib import Path

from loguru import logger

from platform_input_support.action.action import Action


class ActionRepository:
    def __init__(self):
        self.actions: dict[str, type[Action]] = {}

    @staticmethod
    def _filename_to_class(filename: str) -> str:
        return filename.replace('_', ' ').title().replace(' ', '')

    def _register_action(self, action_name: str, action: type[Action]):
        self.actions[action_name] = action
        logger.debug(f'registered action {action_name}')

    def register_actions(self):
        actions_dir = Path(__file__).parent.parent / 'actions'
        logger.debug(f'registering actions from {actions_dir}')

        for file_path in actions_dir.glob('*.py'):
            filename = file_path.stem
            action_module = import_module(f'platform_input_support.actions.{filename}')

            if action_module.__spec__ is None:
                continue

            for name, obj in getmembers(action_module):
                if isclass(obj) and name == self._filename_to_class(filename):
                    self._register_action(filename, obj)
                    break


action_repository = ActionRepository()
action_repository.register_actions()

from platform_input_support.task.task import PreTask, Task
from platform_input_support.task.task_registry import TaskRegistry

PREPROCESS_TASKS = ['explode', 'get_file_list']

task_registry = TaskRegistry()
task_registry.register_tasks()

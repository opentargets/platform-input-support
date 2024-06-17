from platform_input_support.task.task import Task
from platform_input_support.task.task_repository import TaskRepository

PREPROCESS_TASKS = ['explode', 'get_file_list']

task_repository = TaskRepository()
task_repository.register_tasks()

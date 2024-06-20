from platform_input_support.config.config import Config

c = Config()

settings = c.settings
task_definitions = c.step_definitions[settings.step]
scratchpad = c.scratchpad

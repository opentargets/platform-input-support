import ast
from string import Template

from platform_input_support.config import scratch_pad


class TemplateWithDots(Template):
    idpattern = r'(?a:[_a-z][._a-z0-9]*)'


class ScratchPad:
    def __init__(self, sentinel_dict: dict | None):
        self.sentinel_dict = sentinel_dict or {}

    def store(self, key: str, value: str | list[str]):
        self.sentinel_dict[key] = value

    def replace(self, template: str) -> str:
        replacer = TemplateWithDots(template)
        replaced_value = replacer.substitute(self.sentinel_dict)

        try:
            parsed_value = ast.literal_eval(replaced_value)
        except (SyntaxError, ValueError):
            parsed_value = replaced_value

        return parsed_value


scratch_pad = ScratchPad(scratch_pad)

import ast
from pathlib import Path
from string import Template
from typing import Any

from platform_input_support.util.errors import ScratchpadError


class TemplateWithDots(Template):
    idpattern = r'(?a:[_a-z][._a-z0-9]*)'


class Scratchpad:
    """A class to store and replace placeholders in strings.

    This class is used to store key-value pairs and replace placeholders in
    strings with the corresponding values. The placeholders are defined in the
    strings using the dollar sign followed by the placeholder name enclosed in
    curly braces, e.g., `${person.name}`. The placeholders can have dots in
    their names to represent nested dictionaries or objects.

    Example:
        >>> scratchpad = Scratchpad()
        >>> scratchpad.store('person.name', 'Alice')
        >>> scratchpad.replace('Hello, ${person.name}!')
        'Hello, Alice!'

    Args:
        sentinel_dict (dict[str, Any], optional): A dictionary with the initial
        key-value pairs to store in the scratchpad. Defaults to `None`.
    """

    def __init__(self, sentinel_dict: dict[str, Any] | None = None):
        self.sentinel_dict = sentinel_dict or {}

    def store(self, key: str, value: str | list[str]):
        """Store a key-value pair in the scratchpad.

        Both strings and lists of strings are accepted as values. It might be
        useful to extend it to accept dicts as well.

        Args:
            key (str): The key to store.
            value (str | list[str]): The value to store.
        """
        self.sentinel_dict[key] = value

    def replace(self, sentinel: str | Path) -> str:
        """Replace placeholders in a string with the corresponding values.

        Args:
            sentinel (str): The string with placeholders to replace.

        Returns:
            str: The string with the placeholders replaced by their values.

        Raises:
            ScratchpadError: If a placeholder in the string does not have a
                corresponding value in the scratchpad.
        """
        replacer = TemplateWithDots(str(sentinel))

        try:
            replaced_value = replacer.substitute(self.sentinel_dict)
        except KeyError:
            raise ScratchpadError(sentinel)

        try:
            parsed_value = ast.literal_eval(replaced_value)
        except (SyntaxError, ValueError):
            parsed_value = replaced_value

        return parsed_value

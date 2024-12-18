"""Scratchpad module.

This module defines the `Scratchpad` class, which is a centralized place to store
key-value pairs in the configuration of the application. It provides utilities to
perform template substition.
"""

import ast
from pathlib import Path
from string import Template
from typing import Any

from pis.util.errors import ScratchpadError


class TemplateWithDots(Template):
    """A subclass of `string.Template` that allows dots in placeholders."""

    idpattern = r'(?a:[_a-z][._a-z0-9]*)'


class Scratchpad:
    """A class to store and replace placeholders in strings.

    This class is used to store key-value pairs and replace placeholders in strings with
    the corresponding values. The placeholders are defined in the strings using the dollar
    sign followed by the placeholder name enclosed in curly braces, e.g., `${person.name}`.
    The placeholders can have dots in their names to represent nested dictionaries or objects.

    Example:
        >>> scratchpad = Scratchpad()
        >>> scratchpad.store('person.name', 'Alice')
        >>> scratchpad.replace('Hello, ${person.name}!')
        'Hello, Alice!'

    :ivar sentinel_dict: A dictionary to store the key-value pairs.
    :vartype sentinel_dict: dict[str, Any]
    """

    def __init__(self, sentinel_dict: dict[str, Any] | None = None):
        self.sentinel_dict = sentinel_dict or {}

    def store(self, key: str, value: str | list[str]):
        """Store a key-value pair in the scratchpad.

        Both strings and lists of strings are accepted as values. It might be
        useful to extend it to accept dicts as well.

        :param key: The key to store.
        :type key: str
        :param value: The value to store.
        :type value: str | list[str]
        """
        self.sentinel_dict[key] = value

    def replace(self, sentinel: str | Path) -> str:
        """Replace placeholders in a string with the corresponding values.

        :param sentinel: The string with placeholders to replace.
        :type sentinel: str | Path
        :return: The string with the placeholders replaced by their values.
        :rtype: str
        :raises ScratchpadError: If a placeholder in the string does not have a
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

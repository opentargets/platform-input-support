import pytest

from pis.config.scratchpad import Scratchpad, ScratchpadError


def test_store_string():
    scratchpad = Scratchpad()

    scratchpad.store('key1', 'value1')

    assert scratchpad.sentinel_dict['key1'] == 'value1'


def test_store_list():
    scratchpad = Scratchpad()

    scratchpad.store('key2', ['value2', 'value3'])

    assert scratchpad.sentinel_dict['key2'] == ['value2', 'value3']


def test_replace_simple_substitution():
    scratchpad = Scratchpad()

    scratchpad.store('name', 'world')
    result = scratchpad.replace('Hello, $name!')

    assert result == 'Hello, world!'


def test_replace_with_dot_notation():
    scratchpad = Scratchpad()

    scratchpad.store('user.name', 'John Doe')
    result = scratchpad.replace('Name: $user.name')

    assert result == 'Name: John Doe'


def test_replace_missing_key():
    scratchpad = Scratchpad()

    scratchpad.store('exists', 'yes')

    with pytest.raises(ScratchpadError):
        scratchpad.replace('Missing: $missing')


def test_replace_invalid_syntax():
    scratchpad = Scratchpad()

    scratchpad.store('invalid', 'value1, value2')
    result = scratchpad.replace('$invalid')

    assert result == 'value1, value2'

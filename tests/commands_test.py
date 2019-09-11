from pytest import raises

from server.commands import command
from server.commands.commands import Command, commands
from server.exc import InvalidArgument


class Works(Exception):
    pass


class Failed(Exception):
    pass


def cmd(arg):
    if arg is True:
        raise Works
    raise Failed


def test_command():
    c = command()(cmd)
    assert isinstance(c, Command)
    assert c.func is cmd
    with raises(Works):
        c.call(arg=True)
    with raises(Failed):
        c.call(arg=False)
    with raises(InvalidArgument) as exc:
        c.call()
    assert exc.value.args == ('arg',)


def test_custom_name_description():
    name = 'custom name'
    description = ' This is a test description.'
    c = command(name=name, description=description)(cmd)
    assert c.name == name
    assert c.description == description
    assert c.func is cmd
    assert commands[name] is c

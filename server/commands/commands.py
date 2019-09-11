"""Provides the commands dictionary which contains the commands websockets can
run."""

from enum import Enum
from inspect import signature, _empty, getdoc

from attr import attrs, attrib, Factory

from ..exc import InvalidArgument


class LocationTypes(Enum):
    """Valid location types for use with commands."""

    any = 0
    not_map = 1
    map = 2
    not_template = 3
    template = 4
    not_finalised = 5
    finalised = 6


@attrs
class Command:
    """A command which can be run by a client."""

    name = attrib()
    description = attrib()
    func = attrib()
    hotkey = attrib()
    location_type = attrib()
    login_required = attrib()
    admin = attrib()
    args = attrib(default=Factory(dict), init=False)

    def __attrs_post_init__(self):
        s = signature(self.func)
        self.args = {p.name: p.default for p in s.parameters.values()}

    def call(self, **kwargs):
        """Call self.func with the arguments it requires."""
        args = []
        for name, default in self.args.items():
            value = kwargs.get(name, default)
            if value is _empty:
                raise InvalidArgument(name)
            args.append(value)
        return self.func(*args)


commands = {}


def command(
    hotkey=None, location_type=LocationTypes.map, login_required=True,
    name=None, description=None, admin=False
):
    """A decorator to add a new command.

    The location_type argument must be specified as one of the members of the
    LocationType enum to indicate where this command will be valid.

    If login_required evaluates to True, the player must be logged in to use
    the command.

    If a hotkey is provided, then it will be added to the list of hotkeys which
    will be sent as part of the constants.js web route.

    You can provide name and description arguments, to override those found in
    func.__name__, and func.__doc__ respectively.

    If admin evaluates to True, then the command can only be run by
    administrators."""

    def inner(func):
        if name is None:
            _name = func.__name__
        else:
            _name = name
        if description is None:
            _description = getdoc(func)
        else:
            _description = description
        cmd = Command(
            _name, _description, func, hotkey, location_type, login_required,
            admin
        )
        commands[_name] = cmd
        return cmd

    return inner

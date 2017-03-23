"""Commands system."""

import re
from attr import attrs, attrib, Factory
from .help import game_help, command_help
from .building import buildings


@attrs
class Command:
    """A command which can be called by clients."""

    name = attrib()
    pattern = attrib()
    func = attrib()
    doc = attrib(default=Factory(lambda: None))

    def __attrs_post_init__(self):
        self.regexp = re.compile(self.pattern)
        if self.doc is None:
            self.doc = self.func.__doc__


commands = [
    Command(
        'quit',
        '^quit$',
        lambda player, match: player.disconnect(),
        doc='Disconnects you from the game.'
    ),
    Command(
        'help',
        '^help$',
        game_help
    ),
    Command(
        'help <command>',
        '^help ([^$]+)$',
        command_help
    ),
    Command(
        'buildings',
        '^buildings$',
        buildings
    )
]

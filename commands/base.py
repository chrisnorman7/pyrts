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
        if self.pattern is None:
            self.pattern = '^%s$' % self.name
        self.regexp = re.compile(self.pattern)
        if self.doc is None:
            self.doc = self.func.__doc__


commands = [
    Command(
        'quit',
        None,
        lambda player, match: player.disconnect(),
        doc='Disconnects you from the game.'
    ),
    Command(
        'help',
        None,
        game_help
    ),
    Command(
        'help <command>',
        '^help ([^$]+)$',
        command_help
    ),
    Command(
        'buildings',
        None,
        buildings
    ),
    Command(
        'gold',
        None,
        lambda player, match: player.notify(
            'You have {} gold.',
            player.gold
        ),
        doc='Shows you how much gold you have.'
    ),
    Command(
        'wood',
        None,
        lambda player, match: player.notify(
            'You have {} wood.',
            player.wood
        ),
        doc='Shows you how much wood you have.'
    ),
    Command(
        'water',
        None,
        lambda player, match: player.notify(
            'You have {} water.',
            player.water
        ),
        doc='Shows you how much water you have.'
    )
]

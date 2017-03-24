"""Commands system."""

import re
from attr import attrs, attrib, Factory
from .help import game_help, command_help
from .player import buildings, mobiles, name, say, shout, emote, who, menu, \
     tell


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
        'mobiles',
        None,
        mobiles
    ),
    Command(
        'name',
        '^name([^$]*)$',
        name
    ),
    Command(
        'menu',
        '^menu ([^$]+)$',
        menu
    ),
    Command(
        'say <text>',
        '^(say |[\'])([^$]+)$',
        say
    ),
    Command(
        'shout <text>',
        '^(shout |[!])([^$]+)$',
        shout
    ),
    Command(
        'emote <action>',
        '^(emote |[:])([^$]+)$',
        emote
    ),
    Command(
        'who',
        None,
        who
    ),
    Command(
        'tell <object> to <action>[ <argument>]',
        '^tell (?P<object>.+) to (?P<command>[^ $]+)[ ]?(?P<argument>[^$]*)$',
        tell
    ),
]

for attr in ['food', 'water', 'gold', 'wood']:
    commands.append(
        Command(
            attr,
            None,
            lambda player, match, attr=attr: player.notify(
                'You have {} {}.',
                getattr(player, attr),
                attr
            ),
            doc='Shows how much %s you have.' % attr
        )
    )

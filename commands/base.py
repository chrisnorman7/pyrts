"""Commands system."""

import re
from attr import attrs, attrib, Factory
from .help import game_help, command_help
from .player import buildings, mobiles, name, say, shout, emote, who, menu, \
     tell
from .authentication import create, connect


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


quit_command = Command(
    'quit',
    None,
    lambda player, match: player.disconnect(),
    doc='Disconnects you from the game.'
)

game_help_command = Command(
    'help',
    None,
    game_help
)
command_help_command = Command(
    'help <command>',
    '^help ([^$]+)$',
    command_help
)

# Commands everyone can access:
general_commands = [
    quit_command,
    game_help_command,
    command_help_command,
]

# Commands available to logged in players:
commands = [
    *general_commands,
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


# Commands available to players who are not logged in:
anonymous_commands = [
    *general_commands,
    Command(
        'create <username>[ <password>]',
        '^create (?P<username>[^ $]+)(?P<password>[^$]*)$',
        create
    ),
    Command(
        'connect <username> <password>',
        '^connect (?P<username>[^ ]+) (?P<password>[^$]+)$',
        connect
    )
]

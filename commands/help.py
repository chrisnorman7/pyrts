"""Help commands."""

from . import base


def game_help(player, match, commands=None):
    """Get help on game commands."""
    if commands is None:
        player.notify('*** Help ***')
    if commands is None:
        commands = base.commands
    for command in commands:
        player.notify(command.name)
        player.notify(command.doc or 'No help available.')
        player.notify('')


def command_help(player, match):
    """Get help on a specific command."""
    name = match.groups()[0]
    for command in base.commands:
        if command.name.lower().startswith(name.lower()):
            game_help(player, match, commands=[command])
            break
    else:
        player.notify('There is no command with that name.')

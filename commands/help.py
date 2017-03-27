"""Help commands."""


def game_help(player, match, commands=None):
    """Get help on game commands."""
    if commands is None:
        player.notify('*** Help ***')
    if commands is None:
        commands = player.connection.get_commands()
    for command in sorted(commands, key=lambda x: x.name):
        player.notify(command.name)
        player.notify(command.doc or 'No help available.')
        player.notify('')


def command_help(player, match):
    """Get help on a specific command."""
    name = match.groups()[0]
    for command in player.connection.get_commands():
        if command.name.lower().startswith(name.lower()):
            game_help(player, match, commands=[command])
            break
    else:
        player.notify('There is no command with that name.')

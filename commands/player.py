"""Player-related commands."""


def name(player, match):
    """Shows or sets your name."""
    name = match.groups()[0].strip()
    if name:
        player.name = name
        try:
            player.save()
        except Exception as e:
            return player.notify('You cannot set your name to {}.', name)
    player.notify('Your name is {}.', player.name)

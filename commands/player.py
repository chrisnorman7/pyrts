"""Player-related commands."""

from datetime import datetime
from db import session, Player


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


def say(player, match):
    """Say something to the rest of the game."""
    text = match.groups()[1].strip()
    for obj in player.game.players:
        obj.notify('{} says: {}', player.name, text)


def shout(player, match):
    """Shout something to everyone else connected to the server, not just the
    other players in your game."""
    text = match.groups()[1].strip()
    for obj in session.query(Player):
        obj.notify('{} shouts: {}', player.name, text)


def emote(player, match):
    """Emote something to the rest of your game."""
    text = match.groups()[1].strip()
    for obj in player.game.players:
        obj.notify('{} {}', player.name, text)


def who(player, match):
    """Shows everyone who's currently logged in."""
    player.notify('Who listing:')
    now = datetime.now()
    for obj in session.query(Player):
        host = obj.connection.transport.getHost()
        player.notify(
            '{} [{}:{}] connected to {} since {} ({}).',
            obj.name,
            host.host,
            host.port,
            obj.game,
            obj.connection.connected,
            now - obj.connection.connected
        )
    player.end_output()

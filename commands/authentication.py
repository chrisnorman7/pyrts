"""Login commands."""

from random_password import random_password
from twisted.python import log
from credentials import create_player, authenticate
from config import password_length
from .games_menu import games
from util import player_joined


def _connect(player, connection, created=False):
    """Connect connection to player."""
    connection.player = player
    player.connection = connection
    player.notify(
        'Welcome {}, {}.',
        'to the game' if created else 'back',
        player.name
    )
    if player.game:
        player_joined(player)
    else:
        games(player, None)


def create(player, match):
    """Create a player."""
    args = match.groupdict()
    username = args['username']
    password = args['password'].strip()
    if password:
        generated = False
    else:
        generated = True
        password = random_password(length=password_length)
    try:
        p = create_player(username, password)
        if generated:
            player.notify('Password is {}.', password)
        _connect(p, player.connection, created=True)
    except Exception as e:
        log.err(e)
        player.notify(
            'Could not create a player with that username and password '
            'combination.'
        )


def connect(player, match):
    """Login a player."""
    args = match.groupdict()
    username = args['username']
    password = args['password']
    p = authenticate(username, password)
    if p is None:
        player.notify('Invalid username or password.')
    else:
        _connect(p, player.connection)

"""Games commands. These commands are for when the player has authenticated,
but not yet selected or created a game."""

from random import random
from math import floor
from db import Game, Player
from util import match as _match, match_object, player_joined, player_left


def _connect(player, game):
    """Connect player to game."""
    if player.game is not None:
        player_left(player)
    player.game = game
    player.save()
    while 1:
        for attr in ['x', 'y']:
            setattr(
                player,
                attr,
                float(floor(random() * getattr(game, 'size_%s' % attr)))
            )
        player.save()
        if not _match(
            Player,
            Player.id != player.id,
            x=player.x,
            y=player.y
        ).count():
            break
    player_joined(player)


def create_game(player, match):
    """Create a game."""
    name = match.groups()[0]
    m = match_object(Game, name)
    if m.count():
        player.notify(
            'There is already a game named {} on this server.',
            m.first().name
        )
    else:
        g = Game(name=name)
        _connect(player, g)


def join_game(player, match):
    """Connect to an existing game."""
    name = match.groups()[0]
    m = match_object(Game, name)
    c = m.count()
    if not c:
        player.notify('There is no game with the name {}.', name)
    elif c == 1:
        _connect(player, m.first())
    else:
        player.notify(
            'Please be more specific. There are {} games matching {}.',
            c,
            name
        )


def games(player, match):
    """List all games."""
    player.notify('JOIN a game (or CREATE a new one):')
    for g in _match(Game):
        if len(g.players) < g.max_players:
            player.notify(
                '{} ({})',
                g.name or '<Untitled>',
                ', '.join(
                    x.name for x in g.players
                ) if g.players else '<Empty>'
            )
    player.end_output()

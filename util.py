"""Utility functions."""

from sqlalchemy import func
import db


def match(cls, *args, **kwargs):
    """Low level match routine."""
    return db.session.query(cls).filter(*args).filter_by(**kwargs)


def match_object(cls, name, *args, **kwargs):
    """This is a thin wrapper around the match function which takes a name
    argument. This argument is stripped and converted to lower case then added
    to the query with sqlalchemy.func.lower."""
    return match(
        cls,
        func.lower(cls.name).startswith(name.strip().lower()),
        *args,
        **kwargs
    )


def object_created(obj):
    """Alert clients that an object has been created."""
    for player in obj.game.players:
        player.notify('{} created at ({}, {}).', obj.name, obj.x, obj.y)


def object_removed(obj):
    """Object obj was removed from it's game."""
    for p in obj.game.players:
        p.notify('{} has gone from ({}, {}).', obj.name, obj.x, obj.y)


def notify_player(player, string, *args, **kwargs):
    """Notify a player of something."""
    if player.connected:
        player.connection.sendLine(string.format(*args, **kwargs).encode())


def player_joined(player):
    """Player player has just joined a game."""
    player.notify('Game: {}', player.game.name)
    for p in player.game.players:
        p.notify(
            '{} has connected at ({}, {}).',
            player.name,
            player.x,
            player.y
        )


def player_left(player):
    """The specified player has left their game. Perform cleanup."""
    if len(player.game.players) == 1:
        # This game will be empty when player leaves.
        for o in player.game.objects:
            db.session.delete(o)
        db.session.delete(player.game)
    else:
        for p in match(
            db.Player,
            db.Player.id != player.id,
            game=player.game
        ):
            p.notify('{} has left the game.', player)
    player.game = None
    player.save()
    for o in player.owned_objects:
        object_removed(o)
        db.session.delete(o)
    db.session.commit()

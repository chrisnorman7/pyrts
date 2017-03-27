"""Utility functions."""

from sqlalchemy import func
import db


def match_object(name, *args, player=None, type_flag=None):
    """Match an object by name. Extra *args are passed to .filter."""
    if player is None:
        objects = db.session.query(db.GameObject)
    else:
        objects = db.session.query(db.GameObject).filter_by(owner=player)
    if type_flag is not None:
        objects = objects.filter_by(type_flag=type_flag)
    return objects.filter(
        *args,
        func.lower(db.GameObject.name).startswith(name.strip().lower())
    )


def object_created(obj):
    """Alert clients that an object has been created."""
    for player in obj.game.players:
        player.notify('{} created at ({}, {}).', obj.name, obj.x, obj.y)


def notify_player(player, string, *args, **kwargs):
    """Notify a player of something."""
    if player.connected:
        player.connection.sendLine(string.format(*args, **kwargs).encode())

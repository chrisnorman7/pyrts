"""Building commands."""

from db import session, GameObject
from objects import TYPE_BUILDING


def buildings(player, match):
    """Shows a list of your buildings."""
    player.notify('*** Buildings ***')
    for obj in session.query(
        GameObject
    ).filter_by(
        owner=player,
        type_flag=TYPE_BUILDING
    ):
        player.notify(
            '{} at ({}, {}): {}/{}HP.',
            obj.name,
            obj.x,
            obj.y,
            obj.type.max_hp if obj.hp is None else obj.hp,
            obj.type.max_hp
        )
    player.notify('---')

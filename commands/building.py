"""Building commands."""

from db import session, GameObject
from objects import TYPE_BUILDING


def match_building(player, name):
    """Match a building by name."""
    for building in session.query(
        GameObject
    ).filter_by(
        owner=player
    ):
        if building.name.lower().startswith(name.strip().lower()):
            yield building


def buildings(player, match):
    """Shows a list of your buildings."""
    player.notify('*** Buildings ***')
    for obj in session.query(
        GameObject
    ).filter_by(
        owner=player,
        game=player.game,
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
    player.end_output()


def menu(player, match):
    """Show the menu for a particular building."""
    name = match.groups()[0].strip().lower()
    buildings = list(match_building(player, name))
    if not buildings:
        player.notify('No building named {}.', name)
    elif len(buildings) > 1:
        player.notify(
            'Please be more specific. {} buildings were found matching {}.',
            len(buildings),
            name
        )
    else:
        building = buildings[0]
        player.notify('Menu for {}.', building.name)
        for mobile in building.type.provides:
            player.notify('recruit {}', mobile.name)
        player.end_output()

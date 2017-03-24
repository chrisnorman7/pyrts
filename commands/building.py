"""Building commands."""

from sqlalchemy import func
from db import session, GameObject
from objects import TYPE_BUILDING


def match_object(player, type_flag, name):
    """Match a building by name."""
    return session.query(
        GameObject
    ).filter_by(
        owner=player
    ).filter(
        func.lower(GameObject.name).startswith(name.strip().lower())
    )


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
    buildings = list(match_object(player, TYPE_BUILDING, name))
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


def tell(player, match):
    """Give an object an instruction. For example:
    tell town hall recruit labourer
    tell labourer build town hall
    You can get the instructions with the menu command.
    """
    
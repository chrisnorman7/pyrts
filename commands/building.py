"""Building commands."""

from sqlalchemy import func
from db import session, GameObject
from objects import TYPE_BUILDING


def match_object(name, player=None, type_flag=None):
    """Match a building by name."""
    if player is None:
        objects = session.query(GameObject)
    else:
        objects = session.query(GameObject).filter_by(owner=player)
    if type_flag is not None:
        objects = objects.filter_by(type_flag=type_flag)
    return objects.filter(
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
    buildings = match_object(name, type_flag=TYPE_BUILDING, player=player)
    c = buildings.count()
    if not c:
        player.notify('No building named {}.', name)
    elif c > 1:
        player.notify(
            'Please be more specific. {} buildings were found matching {}.',
            c,
            name
        )
    else:
        building = buildings.first()
        player.notify('Menu for {}.', building.name)
        for mobile in building.type.provides:
            player.notify('recruit {}', mobile.name)
        player.end_output()


def tell(player, match):
    """Give an object an instruction. For example:
    tell town hall to recruit labourer
    tell labourer to build town hall
    You can get the instructions with the menu command."""
    args = match.groupdict()
    name = args['object']
    command = args['command']
    command_argument = args['argument']
    objects = match_object(name, player=player)
    c = objects.count()
    if not c:
        player.notify('No objects found matching {}.', name)
    elif c > 1:
        player.notify(
            'Please be more specific. {} objects were found matching {}.',
            c,
            name
        )
    else:
        obj = objects.first()
        obj.commands.get(
            command,
            lambda argument, command=command: player.notify(
                'There is no command {} for {}.',
                command,
                obj.name
            )
        )(command_argument)

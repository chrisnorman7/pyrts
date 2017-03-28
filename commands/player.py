"""Player-related commands."""

from datetime import datetime
from db import session, Player, GameObject
from util import match as _match, match_object, player_left
from buildings import building_types
from objects import commodities, TYPE_BUILDING, TYPE_MOBILE
from mobiles import skills
from .games_menu import games


def buildings(player, match):
    """Shows a list of your buildings."""
    player.notify('Buildings:')
    for obj in session.query(
        GameObject
    ).filter_by(
        owner=player,
        game=player.game,
        type_flag=TYPE_BUILDING
    ):
        player.notify(str(obj))
    player.end_output()


def mobiles(player, match):
    """Shows a list of your mobiles."""
    player.notify('Mobiles:')
    for obj in session.query(GameObject).filter_by(
        game=player.game,
        owner=player,
        type_flag=TYPE_MOBILE
    ):
        player.notify(str(obj))
    player.end_output()


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
    for obj in _match(Player):
        host = obj.connection.transport.getPeer()
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


def tell(player, match):
    """Give an object an instruction. For example:
    tell town hall to recruit labourer
    tell labourer to build town hall
    You can get the instructions with the menu command."""
    args = match.groupdict()
    name = args['object']
    command = args['command']
    command_argument = args['argument']
    objects = match_object(GameObject, name, owner=player)
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
            lambda player, obj, argument, command=command: player.notify(
                'There is no command {} for {}.',
                command,
                obj.name
            )
        )(player, obj, command_argument)


def menu(player, match):
    """Show the menu for a particular object."""
    name = match.groups()[0].strip().lower()
    objects = match_object(GameObject, name, owner=player)
    c = objects.count()
    if not c:
        player.notify('No object named {}.', name)
    elif c > 1:
        player.notify(
            'Please be more specific. {} objects were found matching {}.',
            c,
            name
        )
    else:
        obj = objects.first()
        player.notify('Menu for {}.', obj.name)
        if obj.type_flag == TYPE_BUILDING:
            for mobile in obj.type.provides:
                player.notify(
                    'recruit {} ({})',
                    mobile.name,
                    ', '.join(
                        [
                            '{} {}'.format(
                                getattr(mobile, attr),
                                attr
                            ) for attr in commodities
                        ]
                    )
                )
        elif obj.type_flag == TYPE_MOBILE:
            buildings = session.query(
                GameObject
            ).filter_by(
                game=player.game,
                owner=player
            )
            if obj.type.skills & skills['build']:
                for building in building_types.values():
                    if not building.depends or buildings.filter(
                        GameObject.type_flag.in_(
                            [x.type_flag for x in building.depends]
                        )
                    ).count():
                        player.notify('build {}', building.name)
            loc = obj.location
            if loc is not None:
                for attr in commodities:
                    if getattr(loc, attr) and obj.type.skils & skills[attr]:
                        player.notify('collect {}', attr)
        player.end_output()


def leave(player, match):
    """Leave your current game."""
    player_left(player)
    player.game = None
    player.save()
    games(player, None)

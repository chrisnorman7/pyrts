"""Provides general commands for logging in ETC."""

from .commands import command, commands, LocationTypes

from ..db import Map, Player
from ..exc import InvalidUsername, InvalidPassword
from ..menus import Menu
from ..options import volume_adjust
from ..util import english_list


@command(location_type=LocationTypes.any, login_required=False)
def authenticate(con, username, password):
    """Try to authenticate."""
    try:
        p = Player.authenticate(username, password)
        p.connection = con
    except InvalidPassword:
        con.message('Invalid login.')
    except InvalidUsername:
        p = Player.create(username, password, 'New Player')
        p.save()
        p.connection = con
        if Player.count() == 1:
            p.admin = True
            con.message('Making you an administrator.')
            p.save()


@command(location_type=LocationTypes.any, hotkey='f1')
def main_menu(con, player, location):
    """Show the main menu."""
    m = Menu('Main Menu', dismissable=True)
    m.add_label('Actions')
    m.add_item('Change Your Name', 'rename_player')
    if location is None:
        m.add_label('Games')
        m.add_item('Start Game', 'start_game')
        for map in Map.query(finalised=None, template=False):
            name = f'{map.name} (with {english_list(map.players)})'
            m.add_item(name, 'join_map', args={'id': map.id})
        m.add_label('Map Creation')
        m.add_item('New Map', 'create_map')
        q = Map.query(owner=player, template=True)
        c = q.count()
        if c:
            m.add_label(f'Edit Map ({c})')
            for map in q:
                m.add_item(map.name, 'join_map', args=dict(id=map.id))
    else:
        if location.template:
            m.add_item('Rename Map', 'rename_map')
        m.add_item('Leave Map', 'leave_map')
    m.send(con)


@command(location_type=LocationTypes.any)
def rename_player(con, player, text=None):
    """Rename your player."""
    if text:
        if not Player.query(name=text).count():
            player.name = text
            player.save()
            player.message(f'You will now be known as {player.name}.')
            con.send('authenticated', text)
        else:
            player.message('That name is already taken.')
    else:
        con.text('Character name', 'rename_player', value=player.name)


@command(location_type=LocationTypes.any, hotkey='shift+?')
def help(con):
    """Show a list of all the possible hotkeys."""
    for cmd in sorted(
        (x for x in commands.values() if x.hotkey is not None),
        key=lambda command: command.hotkey
    ):
        con.message(f'{cmd.hotkey}:')
        con.message(cmd.description)


@command(location_type=LocationTypes.any, hotkey='f9')
def volume_down(player):
    """Set sound volume."""
    player.volume = max(0.0, player.volume - volume_adjust)
    player.save()
    player.send_volume()


@command(location_type=LocationTypes.any, hotkey='f10')
def volume_up(player):
    """Set sound volume."""
    player.volume = min(1.0, player.volume + volume_adjust)
    player.save()
    player.send_volume()

"""Administrative commands."""

from .commands import command

from ..db import Player
from ..menus import YesNoMenu


@command(admin=True)
def disconnect(con, command_name, player, args, id, response=None):
    """Disconnect another player."""
    p = Player.get(id)
    if p is None:
        con.message('Invalid ID.')
    elif response is None:
        m = YesNoMenu(
            f'Are you sure you want to disconnect {p}?', command_name,
            args=args
        )
        m.send(con)
    elif response:
        if not p.connected:
            con.message('They are already disconnected.')
        else:
            p.message(f'You have been booted off the server by {player}.')
            p.disconnect()
    else:
        con.message('Cancelled.')


@command(admin=True)
def delete_player(con, command_name, player, args, id, response=None):
    """Delete another player."""
    p = Player.get(id)
    if p is None:
        con.message('Invalid ID.')
    elif response is None:
        m = YesNoMenu(
            f'Are you sure you want to delete {p}?', command_name, args=args
        )
        m.send(con)
    elif response:
        p.message(f'You have been deleted by {player}.')
        p.disconnect()
        p.delete()
        player.message('Done.')
    else:
        player.message('Cancelled.')


@command(admin=True)
def make_admin(player, id):
    """Make another player an administrator."""
    p = Player.get(id)
    if p is None:
        player.message('Invalid ID.')
    else:
        p.admin = True
        player.message(f'{p} is now an admin.')


@command(admin=True)
def revoke_admin(player, id):
    """Revoke admin privileges for another player."""
    p = Player.get(id)
    if p is None:
        player.message('Invalid ID.')
    else:
        p.admin = False
        player.message(f'{p} is no longer an admin.')

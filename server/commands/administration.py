"""Administrative commands."""

from code import InteractiveConsole
from contextlib import redirect_stdout, redirect_stderr

from .commands import command, LocationTypes

from .. import db
from ..menus import YesNoMenu

Player = db.Player
consoles = {}


class Console(InteractiveConsole):
    """A console with updated push and write methods."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in dir(db):
            if not name.startswith('_'):
                self.locals[name] = getattr(db, name)

    def write(self, string):
        """Send the provided string to self.player.message."""
        self.player.message(string)

    def push(self, con, player, location, entry_point, code):
        """Update self.locals, then run the code."""
        self.player = player
        kwargs = con.get_default_kwargs(player, location, entry_point)
        self.locals.update(**kwargs, console=self)
        res = super().push(code)
        for name in kwargs:
            del self.locals[name]
        self.player = None
        return res


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


@command(location_type=LocationTypes.any, admin=True, hotkey='backspace')
def python(command_name, con, player, location, entry_point, text=None):
    """Run some code."""
    if text is None:
        con.text('Code', command_name, value=player.code)
    else:
        player.code = text
        if player.id not in consoles:
            consoles[player.id] = Console()
        c = consoles[player.id]
        with redirect_stdout(c), redirect_stderr(c):
            res = c.push(con, player, location, entry_point, text)
        if res:
            consoles[player.id] = c

"""Administrative commands."""

from code import InteractiveConsole
from contextlib import redirect_stdout, redirect_stderr
from inspect import getdoc, _empty

from sqlalchemy import Boolean, inspect

from .commands import command, LocationTypes

from .. import db
from ..menus import Menu, YesNoMenu

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


@command(hotkey='m', admin=True)
def make_menu(con):
    """Add / remove types."""
    m = Menu('Add / Remove Types')
    for cls in (db.MobileType, db.BuildingType, db.AttackType, db.FeatureType):
        m.add_label(cls.__tablename__.replace('_', ' ').title())
        for action in ('add', 'edit', 'remove'):
            m.add_item(
                action.title(), f'{action}_type', args=dict(cls=cls.__name__)
            )
    m.send(con)


@command(admin=True)
def add_type(player, cls):
    """Add a new type."""
    cls = db.Base._decl_class_registry[cls]
    cls(name='Untitled').save()
    player.message('Done.')


@command(admin=True)
def remove_type(con, command_name, cls, id=None, response=None):
    """Remove a type."""
    cls = db.Base._decl_class_registry[cls]
    if id is None:
        m = Menu('Select Object')
        for obj in cls.all():
            m.add_item(
                obj.get_name(), command_name,
                args=dict(cls=cls.__name__, id=obj.id)
            )
        m.send(con)
    elif response is None:
        m = YesNoMenu(
            'Are you sure?', command_name, args=dict(cls=cls.__name__, id=id)
        )
        m.send(con)
    elif response:
        obj = cls.get(id)
        if obj is None:
            con.message('Invalid type.')
        else:
            obj.delete()
            con.message('Done.')
    else:
        con.message('Cancelled.')


@command(admin=True)
def edit_type(con, command_name, cls, id=None, column=None, text=None):
    """Edit a type."""
    cls = db.Base._decl_class_registry[cls]
    class_name = cls.__name__
    if id is None:
        m = Menu('Objects')
        for obj in cls.all():
            m.add_item(
                obj.get_name(), command_name,
                args=dict(cls=class_name, id=obj.id)
            )
        m.send(con)
    else:
        i = inspect(cls)
        obj = cls.get(id)
        if column is not None:
            c = i.c[column]
            if text is None:
                keys = list(c.foreign_keys)
                if len(keys) == 1:
                    key = keys[0]
                    remote_class = db.Base.get_class_from_table(
                        key.column.table
                    )
                    m = Menu('Select Object')
                    if c.nullable:
                        m.add_item(
                            'NULL', command_name, args=dict(
                                cls=class_name, id=id, column=column, text=''
                            )
                        )
                    for thing in remote_class.all():
                        m.add_item(
                            thing.get_name(), command_name, args=dict(
                                cls=class_name, id=id, column=column,
                                text=str(thing.id)
                            )
                        )
                    return m.send(con)
                value = getattr(obj, column)
                if value is None:
                    value = ''
                else:
                    value = str(value)
                return con.text(
                    'Enter value', command_name, value=value, args=dict(
                        cls=class_name, id=id, column=column
                    )
                )
            else:
                if text == '':  # Same as None.
                    if c.nullable:
                        value = None
                    else:
                        con.message('That column is not nullble.')
                        value = _empty
                else:
                    try:
                        value = c.type.python_type(text)
                    except ValueError:
                        con.message('Invalid value.')
                        value = _empty
                if value is not _empty:
                    setattr(obj, column, value)
                    obj.save()
        m = Menu(obj.get_name())
        m.add_label(getdoc(cls))
        for c in sorted(i.c, key=lambda thing: thing.name):
            if c.primary_key:
                continue
            name = c.name
            title = name.replace('_', ' ').title()
            value = getattr(obj, name)
            keys = list(c.foreign_keys)
            if value is not None:
                if keys:
                    if len(keys) > 1:
                        continue  # Don't mess with that.
                    key = keys[0]
                    remote_class = db.Base.get_class_from_table(key.column.table)
                    value = remote_class.get(value).get_name()
                else:
                    value = repr(value)
            if isinstance(c.type, Boolean):
                new_value = not value
            else:
                new_value = None
            m.add_item(
                f'{title}: {value} [{c.type}]', command_name, args=dict(
                    cls=class_name, id=id, column=name, text=new_value
                )
            )
        m.add_item('Done', command_name, args=dict(cls=class_name))
        m.send(con)

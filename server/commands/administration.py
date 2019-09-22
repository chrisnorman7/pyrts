"""Administrative commands."""

from code import InteractiveConsole
from contextlib import redirect_stdout, redirect_stderr
from inspect import getdoc, _empty

from sqlalchemy import Boolean, inspect

from .commands import command, LocationTypes

from .. import db
from ..db import (
    Player, BuildingType, MobileType, AttackType, FeatureType, Base,
    BuildingRecruit
)
from ..menus import Menu, YesNoMenu
from ..options import options
from ..util import english_list

consoles = {}


class Console(InteractiveConsole):
    """A console with updated push and write methods."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in dir(db):
            if not name.startswith('_'):
                self.locals[name] = getattr(db, name)
        self.locals['options'] = options

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
    for cls in (MobileType, BuildingType, AttackType, FeatureType):
        m.add_label(cls.__tablename__.replace('_', ' ').title())
        for action in ('add', 'edit', 'remove'):
            m.add_item(
                action.title(), f'{action}_type',
                args=dict(class_name=cls.__name__)
            )
    m.send(con)


@command(admin=True)
def add_type(player, class_name):
    """Add a new type."""
    cls = Base._decl_class_registry[class_name]
    cls(name='Untitled').save()
    player.message('Done.')


@command(admin=True)
def remove_type(con, command_name, class_name, id=None, response=None):
    """Remove a type."""
    cls = Base._decl_class_registry[class_name]
    if id is None:
        m = Menu('Select Object')
        for obj in cls.all():
            m.add_item(
                obj.get_name(), command_name,
                args=dict(class_name=class_name, id=obj.id)
            )
        m.send(con)
    else:
        kwargs = dict(class_name=class_name, id=id)
        if response is None:
            m = YesNoMenu('Are you sure?', command_name, args=kwargs)
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
def edit_type(con, command_name, class_name, id=None, column=None, text=None):
    """Edit a type."""
    cls = Base._decl_class_registry[class_name]
    if id is None:
        m = Menu('Objects')
        for obj in cls.all():
            m.add_item(
                obj.get_name(), command_name,
                args=dict(class_name=class_name, id=obj.id)
            )
        m.send(con)
    else:
        i = inspect(cls)
        obj = cls.get(id)
        if column is not None:
            kwargs = dict(class_name=class_name, id=id, column=column)
            c = i.c[column]
            if text is None:
                keys = list(c.foreign_keys)
                if len(keys) == 1:
                    key = keys[0]
                    remote_class = Base.get_class_from_table(
                        key.column.table
                    )
                    m = Menu('Select Object')
                    if c.nullable:
                        null_kwargs = kwargs.copy()
                        null_kwargs['text'] = ''
                        m.add_item('NULL', command_name, args=null_kwargs)
                    for thing in remote_class.all():
                        remote_kwargs = kwargs.copy()
                        remote_kwargs['text'] = str(thing.id)
                        m.add_item(
                            thing.get_name(), command_name, args=remote_kwargs
                        )
                    return m.send(con)
                value = getattr(obj, column)
                if value is None:
                    value = ''
                else:
                    value = str(value)
                return con.text(
                    'Enter value', command_name, value=value, args=kwargs
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
        kwargs = dict(class_name=class_name, id=obj.id)
        for c in sorted(i.c, key=lambda thing: thing.name):
            if c.primary_key:
                continue
            name = c.name
            column_kwargs = kwargs.copy()
            column_kwargs['column'] = name
            title = name.replace('_', ' ').title()
            value = getattr(obj, name)
            keys = list(c.foreign_keys)
            new_value = None
            if value is not None:
                if isinstance(c.type, Boolean):
                    new_value = not value
                if keys:
                    key = keys[0]
                    remote_class = Base.get_class_from_table(
                        key.column.table
                    )
                    value = remote_class.get(value).get_name()
                else:
                    value = repr(value)
            column_kwargs['text'] = new_value
            m.add_item(
                f'{title}: {value} [{c.type}]', command_name,
                args=column_kwargs
            )
        if cls is BuildingType:
            kwargs = dict(building_type_id=obj.id)
            el = english_list(obj.builders, empty='None')
            m.add_item(
                f'Mobile types that can build this building: {el}',
                'edit_builders', args=kwargs
            )
            el = english_list(obj.recruits, empty='None')
            m.add_item(
                f'Mobile types this building can recruit: {el}',
                'edit_recruits', args=kwargs
            )
        elif cls is MobileType:
            m.add_label('Buildings which can be built by units of this type')
            for bt in obj.can_build:
                m.add_item(
                    bt.get_name(), 'edit_type', args=dict(
                        class_name='BuildingType', id=bt.id
                    )
                )
            m.add_label('Buildings which can recruit units of this type')
            for bm in BuildingRecruit.all(mobile_type_id=obj.id):
                bt = BuildingType.get(bm.building_type_id)
                m.add_item(
                    bt.get_name(), 'edit_recruits', args=dict(
                        building_type_id=bt.id, building_mobile_id=bm.id
                    )
                )
        m.add_item('Done', command_name, args=dict(class_name=class_name))
        m.send(con)


@command(admin=True)
def edit_builders(con, command_name, building_type_id, mobile_type_id=None):
    """Add and remove mobile types that can build buildings."""
    bt = BuildingType.get(building_type_id)
    if mobile_type_id is None:
        m = Menu('Mobile Types')
        for mt in MobileType.all():
            if bt in mt.can_build:
                checked = '*'
            else:
                checked = ' '
            m.add_item(
                f'{mt.get_name()} ({checked})', command_name, args=dict(
                    building_type_id=bt.id, mobile_type_id=mt.id
                )
            )
        m.add_item(
            'Done', 'edit_type', args=dict(class_name='BuildingType', id=bt.id)
        )
        m.send(con)
    else:
        mt = MobileType.get(mobile_type_id)
        if mt in bt.builders:
            bt.builders.remove(mt)
            action = 'no longer'
        else:
            bt.builders.append(mt)
            action = 'now'
        con.message(f'{mt.get_name()} can {action} build {bt.get_name()}.')
        con.call_command(command_name, building_type_id=bt.id)


@command(admin=True)
def delete_object(con, command_name, class_name, id=None, response=None):
    """Delete the given object."""
    cls = Base._decl_class_registry[class_name]
    if id is None:
        m = Menu('Objects')
        for obj in cls.all():
            m.add_item(
                str(obj), command_name, args=dict(
                    class_name=class_name, id=obj.id
                )
            )
        m.send(con)
    elif response is None:
        m = YesNoMenu(
            'Are you sure?', command_name, args=dict(
                class_name=class_name, id=id
            )
        )
        m.send(con)
    elif response:
        obj = cls.get(id)
        obj.delete()
        con.message('Done.')
    else:
        con.message('Cancelled.')


@command(admin=True)
def add_recruit(con, command_name, building_type_id, mobile_type_id=None):
    """Add a recruit to the given building type."""
    bt = BuildingType.get(building_type_id)
    if mobile_type_id is None:
        m = Menu('Mobile Types')
        for mt in MobileType.all():
            m.add_item(
                mt.get_name(), command_name, args=dict(
                    building_type_id=bt.id, mobile_type_id=mt.id
                )
            )
        m.send(con)
    else:
        mt = MobileType.get(mobile_type_id)
        bt.add_recruit(mt).save()
        con.call_command('edit_recruits', building_type_id=bt.id)


@command(admin=True)
def edit_recruits(
    con, command_name, building_type_id, building_mobile_id=None,
    resource_name=None, text=None
):
    """Edit recruits for the given building type."""
    columns = inspect(BuildingRecruit).c
    resource_names = BuildingRecruit.resource_names()
    resource_names.append('pop_time')
    bt = BuildingType.get(building_type_id)
    if building_mobile_id is None:
        m = Menu('Recruits')
        m.add_item(
            'Add Recruit', 'add_recruit', args=dict(building_type_id=bt.id)
        )
        for bm in BuildingRecruit.all(building_type_id=bt.id):
            mt = MobileType.get(bm.mobile_type_id)
            m.add_item(
                f'{mt.get_name()}: {bm.resources_string()}', command_name,
                args=dict(building_type_id=bt.id, building_mobile_id=bm.id)
            )
        m.add_item(
            'Done', 'edit_type', args=dict(class_name='BuildingType', id=bt.id)
        )
        m.send(con)
    else:
        bm = BuildingRecruit.get(building_mobile_id)
        kwargs = dict(building_type_id=bt.id, building_mobile_id=bm.id)
        if resource_name is not None:
            if text is None:
                kwargs['resource_name'] = resource_name
                value = getattr(bm, resource_name)
                if value is None:
                    value = ''
                return con.text(
                    'Enter value', command_name, value=value, args=kwargs
                )
            else:
                if not text:
                    if columns[resource_name].nullable:
                        value = None
                    else:
                        con.message('Value cannot be null.')
                        value = _empty
                else:
                    try:
                        value = int(text)
                    except ValueError:
                        con.message('Invalid value.')
                        value = _empty
                if value is not _empty:
                    if resource_name in resource_names:
                        setattr(bm, resource_name, value)
                        bm.save()
                    else:
                        con.message('Invalid resource name.')
        kwargs = dict(building_type_id=bt.id, building_mobile_id=bm.id)
        m = Menu('Recruit Options')
        for name in resource_names:
            resource_kwargs = kwargs.copy()
            resource_kwargs['resource_name'] = name
            value = getattr(bm, name)
            m.add_item(
                f'{name.title()}: {value}', command_name, args=resource_kwargs
            )
        m.add_item(
            'Delete', 'delete_object', args=dict(
                class_name='BuildingRecruit', id=bm.id
            )
        )
        m.add_item(
            'Done', 'edit_type', args=dict(class_name='BuildingType', id=bt.id)
        )
        m.send(con)

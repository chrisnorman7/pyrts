"""Provides map-related commands."""

from random import random, choice

from sqlalchemy import func
from .commands import command, LocationTypes

from ..db import (
    Building, BuildingRecruit, BuildingType, EntryPoint, Feature, FeatureType,
    Map, Unit, UnitType, Player, Base, BuildingBuilder, session
)
from ..menus import Menu, YesNoMenu
from ..options import options
from ..util import pluralise, is_are, english_list, difference_string


@command(location_type=LocationTypes.not_map, admin=True)
def create_map(con, player):
    """Create a new map."""
    m = Map(name='New Map', owner=player)
    m.save()
    player.location = m
    player.location.save()
    player.move(0, 0)
    player.message('Map created in edit mode.')


@command(location_type=LocationTypes.template, hotkey='f2')
def rename_map(con, command_name, location, text=None):
    """Rename the map."""
    if not text:
        con.text('New name for this map', command_name, value=location.name)
    else:
        location.name = text
        location.save()
        con.message('Renamed.')


@command(hotkey='b')
def build(con, location):
    """Add something to a map in edit mode."""
    if not location.template and location.finalised is None:
        return con.message('You cannot use that command here.')
    m = Menu('Build')
    if location.template:
        m.add_label('General')
        m.add_item('Entry Point', 'add_entry_point')
        m.add_label('Land Features')
        for t in FeatureType.alphabetized():
            m.add_item(t.name, 'add_feature', args={'id': t.id})
        m.add_label('Buildings')
    if location.finalised:
        command = 'build_building'
    else:
        command = 'add_building'
    for t in BuildingType.alphabetized():
        if t.depends is None:
            name = t.get_name()
        else:
            name = f'{t.get_name()} (requires {t.depends.get_name()})'
        m.add_item(name, command, args={'id': t.id})
    m.send(con)


@command(location_type=LocationTypes.template, hotkey='a')
def add_entry_point(player, location):
    """Add an entry point to the current map."""
    if EntryPoint.query(location=location, x=player.x, y=player.y).count():
        player.message('There is already an entry point there.')
    else:
        e = location.add_entry_point(player.x, player.y)
        e.save()
        player.message('Entry point created.')


@command(location_type=LocationTypes.template)
def add_building(player, location, con, command_name, id):
    """Add a building."""
    t = BuildingType.get(id)
    if t is None:
        player.message('Invalid ID.')
    else:
        b = location.add_building(t, player.x, player.y)
        b.save()
        player.message(f'{b.get_name()} created.')


@command(location_type=LocationTypes.template)
def add_feature(player, location, con, command_name, id=None):
    """Add a building."""
    if id is None:
        m = Menu('Features')
        for t in FeatureType.alphabetized():
            m.add_item(t.name, command_name, args={'id': t.id})
        m.send(con)
    else:
        type = FeatureType.get(id)
        if type is None:
            return player.message('Invalid ID.')
        f = location.add_feature(type, player.x, player.y)
        f.save()
        player.message(f'{type.name} created.')


def switch_object(player, direction):
    """Select the previous / next object."""
    q = player.visible_objects
    c = len(q)
    if not c:
        return player.message('There is nothing here.')
    try:
        index = q.index(player.focussed_object)
        obj = q[index + direction]
    except (ValueError, IndexError):
        if direction < 0:
            obj = q[-1]
        else:
            obj = q[0]
    player.focussed_object = obj
    player.save()
    if getattr(obj, 'owner', None) is None:
        msg = obj.get_full_name()
    else:
        msg = obj.get_name()
    if isinstance(obj, Unit) and obj.owner is player:
        msg = obj.get_name()
        msg += ' ('
        if obj.selected:
            msg += 'Selected'
        else:
            msg += 'Not selected'
        msg += ')'
    if isinstance(obj, Building) and obj.owner is player:
        msg += f' ({obj.resources_string(empty="empty")})'
    player.message(msg)


@command(hotkey=',')
def previous_object(player):
    """Select the previous object."""
    switch_object(player, -1)


@command(hotkey='.')
def next_object(player):
    """Select the next object."""
    switch_object(player, 1)


@command(location_type=LocationTypes.template, hotkey=';')
def set_resource(con, player, location, command_name, name=None, value=None):
    """Set resources on a land feature."""
    fo = player.focussed_object
    if fo is None:
        player.message('That object is no longer valid.')
    elif not isinstance(fo, Feature):
        player.message('That is not a land feature.')
    elif name is None:
        m = Menu('Resource Types')
        for name in fo.type.resources:
            m.add_item(name, command_name, args={'name': name})
        m.send(con)
    elif value is None:
        con.text(
            'Enter a number', command_name, argument_name='value',
            value=str(getattr(fo, name)),
            args={'name': name}
        )
    elif name not in fo.type.resources:
        player.message('Invalid resource name.')
    elif getattr(fo, name) is None:
        player.message('You cannot set that resource on that feature type.')
    else:
        try:
            value = int(value)
        except ValueError:
            return player .message('Invalid number.')
        setattr(fo, name, value)
        fo.save()
        con.call_command('select_object_0')  # Show them what they did.


@command(hotkey='s')
def stats(player, location):
    """Show resources for this map."""
    for name in sorted(FeatureType.resource_names()):
        col = getattr(Feature, name)
        value = session.query(func.sum(col)).filter_by(
            location=location
        ).first()[0]
        player.message(f'{name.title()}: {value}.')


@command(location_type=LocationTypes.not_map)
def join_map(player, id):
    """Join a new map."""
    m = Map.get(id)
    if m is None:
        player.message('Invalid map ID.')
    else:
        player.location = m
        if m.template:
            player.message(f'You resume editing {m.name}.')
            player.move(0, 0)
        else:
            player.join_map(m)


@command()
def leave_map(con, command_name, player, response=None):
    """Leave the current map."""
    if response is None:
        m = YesNoMenu('Are you sure you want to leave this map?', command_name)
        m.send(con)
    elif response:
        player.leave_map()
        player.save()
    else:
        player.message('Cancelled.')


@command(location_type=LocationTypes.not_map)
def start_game(location, player, con, command_name, id=None):
    """Start a new game."""
    if id is None:
        m = Menu('Maps')
        rm = 'random_map'
        m.add_item('Create Random Map', rm)
        features = {}
        for t in FeatureType.all():
            features[str(t.id)] = 50
        m.add_item(
            'Create Practise Map', rm, args=dict(
                name='Practise Map', players=1, min_resource=20000,
                max_resource=1000000, features=features, done=True
            )
        )
        for map in Map.alphabetized(template=True):
            length = len(map.entry_points)
            if not length:
                continue
            m.add_item(
                f'{map.name} ({length} {pluralise(length, "player")})',
                command_name, args={'id': map.id}
            )
        m.send(con)
    else:
        template = Map.query(template=True, id=id).first()
        if template is None:
            player.message('That map ID is invalid.')
        else:
            m = template.copy()
            m.save()
            player.join_map(m)


@command(location_type=LocationTypes.not_map)
def random_map(
    player, con, command_name, args, name=None, players=None,
    min_resource=None, max_resource=None, features=None, done=False, type=None,
    value=None
):
    """Generate and join a random map."""
    if not name:
        con.text(
            'Enter the name for the map', command_name, argument_name='name',
            args=args
        )
    elif players is None:
        con.text(
            'How many players should be allowed to play this map?',
            command_name, argument_name='players', value=4, args=args
        )
    elif min_resource is None:
        con.text(
            'What is the minimum amount of resources which will go into each '
            'land feature?', command_name, argument_name='min_resource',
            value=0, args=args
        )
    elif max_resource is None:
        con.text(
            'What is the maximum amount of resources which will go into each '
            'land feature?', command_name, argument_name='max_resource',
            value=20000, args=args
        )
    elif not done:
        if features is None:
            features = {str(t.id): 50 for t in FeatureType.all()}
            args['features'] = features
        if type is not None:
            t = FeatureType.get(type)
            if t is None:
                con.message('Invalid type.')
            elif value is None:
                return con.text(
                    'How many of that feature type do you want? (max 100)',
                    command_name, argument_name='value', args=args
                )
            else:
                try:
                    value = int(value)
                    if value > 100:
                        value = 100
                        con.message('Maximum 100.')
                    features[type] = value
                except ValueError:
                    con.message('Invalid value.')
        for name in ('type', 'value'):
            if name in args:
                del args[name]
        m = Menu('Features')
        done_args = args.copy()
        done_args['done'] = True
        m.add_item('Done', command_name, args=done_args)
        for type in FeatureType.alphabetized():
            tid = str(type.id)
            type_args = args.copy()
            type_args['type'] = tid
            if tid not in features:
                features[tid] = 0
            m.add_item(
                f'{type} ({features[tid]})', command_name, args=type_args
            )
        m.send(con)
    else:
        try:
            players = int(players)
            min_resource = int(min_resource)
            max_resource = int(max_resource)
        except ValueError:
            con.message('Invalid value... Please try again.')
            for name in ('players', 'min_resource', 'max_resource'):
                del args[name]
            return con.call_command(command_name, **args)
        con.message('Creating map...')
        _features = {}
        for tid, value in features.items():
            if not value:
                continue
            t = FeatureType.get(tid)
            _features[t] = value
        m = Map.create_random(
            name, players, min_resource, max_resource, _features
        )
        m.save()
        for b in Building.query(location=m).join(Building.type).filter(
            BuildingType.id == options.start_building.id
        ):
            for name in b.resources:
                setattr(b, name, 25)
            b.save()
        player.join_map(m)


def focus_object(hotkey, player):
    """Focus a specific object."""
    if hotkey:
        q = player.visible_objects
        c = len(q)
        if c < hotkey:
            if c:
                player.message(
                    f'There {is_are(c)} only {c} {pluralise(c, "object")}.'
                )
            else:
                player.message('There is nothing here.')
            return
        else:
            player.focussed_object = q[hotkey - 1]
    switch_object(player, 0)


for x in range(10):
    if not x:
        description = 'Show the currently-focused object.'
    else:
        description = f'Select object {x}.'
    command(
        name=f'select_object_{x}', description=description, hotkey=str(x)
    )(lambda player, index=x: focus_object(index, player))


def select_units(index, player):
    """Select a group of units."""
    player.deselect_units()
    if not index:
        group = 'All'
        q = Unit.query(owner=player)
    else:
        types = player.unit_types
        try:
            ut = types[index - 1]
            group = ut.name
            q = Unit.query(owner=player, type=ut)
        except IndexError:
            c = len(types)
            if types:
                player.message(
                    f'There {is_are(c)} only {c} {pluralise(c, "type")} of '
                    'unit.'
                )
            else:
                player.message('There are no units here.')
            return
    c = q.update({Unit.selected: True})
    player.message(f'{group}: {c} {pluralise(c, "unit")} selected.')


def select_unit_list(index, player):
    """Select a unit from a list grouped by types."""
    if not index:
        name = 'All Units'
        kwargs = {}
    else:
        types = player.unit_types
        try:
            type = types[index - 1]
            kwargs = dict(type=type)
            name = f'{type.name} Units'
        except IndexError:
            c = len(types)
            return player.message(
                f'There are only {c} {pluralise(c, "type")} of unit.'
            )
    q = Unit.query(location=player.location, owner=player, **kwargs)
    c = q.count()
    if c:
        m = Menu(name)
        m.add_label(f'Units: {c}')
        for u in q:
            m.add_item(
                f'{u.get_name()} [{u.action_description()}] {u.coordinates}',
                'select_unit',
                args=dict(id=u.id)
            )
            m.send(player.connection)
    else:
        player.message('No units to show.')


def focus_unit(index, player):
    """Focus a unit from a list."""
    q = Unit.query(**player.same_coordinates())
    types = player.unit_types
    c = len(types)
    if not index:
        name = 'All'
    elif index > c:
        return player.message(
            f'There {is_are(c)} only {c} {pluralise(c, "type")} of unit.'
        )
    else:
        ut = types[index - 1]
        q = q.filter_by(type=ut)
        name = f'{ut.get_name()} units'
    if not q.count():
        return player.message('You see no units here.')
    m = Menu(name)
    for u in q:
        m.add_item(
            u.get_name(), 'focus_thing', args=dict(class_name='Unit', id=u.id)
        )
    m.send(player.connection)


for x, hotkey in enumerate('aqwertyuiop'):
    if hotkey == 'a':
        description = 'Select all your units.'
    else:
        description = 'Select a group of units.'
    command(
        name=f'select_units_{hotkey}', description=description, hotkey=hotkey
    )(
        lambda player, index=x: select_units(index, player)
    )
    command(
        name=f'select_unit_list_{hotkey}',
        description='Select a single unit from a list.',
        hotkey=f'shift+{hotkey}'
    )(
        lambda player, index=x: select_unit_list(index, player)
    )
    command(
        name=f'focus_unit_{x}', hotkey=f'alt+ctrl+{hotkey}',
        description='Focus a specific unit from a list'
    )(
        lambda player, index=x: focus_unit(index, player)
    )


@command()
def focus_thing(player, class_name, id):
    """Focus anything on the map, with a class name and an id."""
    cls = Base._decl_class_registry[class_name]
    obj = cls.first(**player.same_coordinates(), id=id)
    if obj is None:
        player.message('You see nothing like that here.')
    else:
        player.focussed_object = obj
        switch_object(player, 0)


@command(location_type=LocationTypes.finalised)
def select_unit(location, player, id):
    """Select a unit by its id."""
    player.deselect_units()
    u = Unit.first(owner=player, location=location, id=id)
    if u is None:
        player.message('That unit does not exist.')
    else:
        u.selected = True
        u.save()
        player.message(f'{u.get_name()} selected.')


@command(location_type=LocationTypes.finalised, hotkey='x')
def toggle_select_unit(player):
    """Select r deselect a unit."""
    fo = player.focussed_object
    if not isinstance(fo, Unit):
        return player.message(f'{fo.get_name()} is not a unit.')
    if fo.selected:
        value = False
        verb = 'Deselect'
    else:
        value = True
        verb = 'Select'
    fo.selected = value
    fo.save()
    player.message(f'{verb}ing {fo.get_name()}.')


@command(location_type=LocationTypes.finalised, hotkey='shift+x')
def deselect_units(player):
    """Deselect all units."""
    player.deselect_units()
    player.message('Unit selections cleared.')


@command(location_type=LocationTypes.finalised, hotkey=' ')
def activate(player, location, con):
    """Show the activation menu for the currently focussed object."""
    m = Menu('Object Menu')
    fo = player.focussed_object
    if fo is not None:
        m.add_label(fo.get_name())
        if isinstance(fo, (Building, Unit)):
            m.add_label(f'{fo.hp} / {fo.max_hp} health')
            if fo.owner is None:
                m.add_item('Acquire', 'acquire', args={'id': fo.id})
            elif isinstance(fo, Unit) and fo.owner is player:
                q = BuildingBuilder.all(unit_type_id=fo.type_id)
                if len(q):
                    m.add_label('Building')
                    for bb in q:
                        t = BuildingType.get(bb.building_type_id)
                        resources = t.resources_string('nothing')
                        m.add_item(
                            f'Build {t.name} (requires {resources}',
                            'build_building', args=dict(id=t.id)
                        )
                if fo.type.transport_capacity is not None:
                    m.add_item('Embark', 'embark')
                    m.add_item('Disembark', 'disembark')
                    m.add_item('Launch', 'launch')
                    m.add_item('File Flight Plan', 'set_destination')
                m.add_item('Release', 'release')
            elif fo.hp < fo.max_hp:  # A sure sign that repairs are needed.
                m.add_item('Repair', 'repair', args=dict(id=fo.id))
        if isinstance(fo, Building) and fo.owner is player:
            for name in BuildingType.resource_names():
                value = getattr(fo, name)
                m.add_label(f'{name.title()}: {value}')
            for br in BuildingRecruit.all(building_type_id=fo.type_id):
                ut = UnitType.get(br.unit_type_id)
                m.add_item(
                    f'Recruit {ut} (requires {br.resources_string()}',
                    'recruit', args=dict(building_recruit_id=ut.id)
                )
            m.add_item('Set Home', 'set_home', args={'id': fo.id})
        if isinstance(fo, (Building, Feature)):
            m.add_item(
                'Exploit', 'exploit', args=dict(
                    id=fo.id, class_name=type(fo).__name__
                )
            )
        if isinstance(fo, Player):
            if player.admin:
                if fo.admin:
                    m.add_item(
                        'Revoke Admin', 'revoke_admin', args={'id': fo.id}
                    )
                else:
                    m.add_item('Make Admin', 'make_admin', args={'id': fo.id})
                if fo.connected:
                    m.add_item('Disconnect', 'disconnect', args={'id': fo.id})
                m.add_item('Delete', 'delete_player', args={'id': fo.id})
    if player.selected_units.count():
        m.add_label('Unit Orders')
        if isinstance(fo, Building):
            m.add_item('Destroy', 'attack')
        if isinstance(fo, Unit):
            m.add_item('Attack', 'attack')
            if fo.health is not None:
                m.add_item('Heal', 'heal', args=dict(unit_id=fo.id))
            m.add_item('Steal', 'steal')
        m.add_item('Summon', 'summon')
        m.add_item('Patrol', 'patrol')
        m.add_item('guard', 'guard')
    m.add_item('Move Entry Point', 'move_entry_point')
    m.send(con)


@command(location_type=LocationTypes.finalised)
def acquire(player):
    """Acquire the currently-focussed object."""
    fo = player.focussed_object
    if fo is None:
        player.message('You must focus an object first.')
    if fo.x != player.x and fo.y != player.y:
        player.message(
            'You can only acquire objects at your current coordinates.'
        )
    elif not isinstance(fo, (Unit, Building)):
        player.message('You can only acquire units and buildings.')
    elif fo.owner is not None:
        player.message('That object has already been acquired.')
    else:
        fo.set_owner(player)
        if isinstance(fo, Unit):
            fo.speak('ready')
        player.message('Done.')


def _recruit(building_id, building_unit_id):
    """Actually perform the recruiting."""
    b = Building.get(building_id)
    if b is None:
        return  # It has since been destroyed.
    bm = BuildingRecruit.get(building_unit_id)
    t = UnitType.get(bm.unit_type_id)
    u = b.location.add_unit(t, *b.coordinates)
    player = b.owner
    u.set_owner(player)
    u.home = b
    u.speak('ready')
    u.save()
    player.message(f'{u.get_name()} ready.')


@command(location_type=LocationTypes.finalised)
def recruit(player, location, building_recruit_id):
    """Recruit a unit."""
    fo = player.focussed_object
    br = BuildingRecruit.get(building_recruit_id)
    ut = UnitType.get(br.unit_type_id)
    d = br.get_difference(fo)
    if not isinstance(fo, Building):
        player.message('You must select a building.')
    elif br.building_type_id != fo.type_id:
        player.message(f'{fo} cannot recruit {ut}.')
    elif fo.health is not None:
        player.message(f'{fo.get_name()} is in no shape for recruitment.')
    elif d:
        player.message(f'You require {difference_string(d)}.')
    else:
        fo.take_requirements(br)
        player.call_later(br.pop_time, _recruit, fo.id, br.id)


@command(location_type=LocationTypes.finalised)
def set_home(player, id):
    """Set the home of all selected units."""
    q = player.selected_units
    b = Building.get(id)
    if b is None or b.owner is not player:
        player.message('Invalid building.')
    else:
        c = q.update({Unit.home_id: id})
        player.message(f'Updated {c} {pluralise(c, "home")}.')


@command(location_type=LocationTypes.finalised)
def exploit(con, args, command_name, player, class_name, id, resource=None):
    """Exploit a feature."""
    cls = Base._decl_class_registry[class_name]
    f = cls.first(id=id, **player.same_coordinates())
    if f is None:
        return player.message('You cannot see that here.')
    elif resource is None:
        if isinstance(f, Feature):
            resources = f.type.resources
        else:
            resources = Building.resource_names()
        if len(resources) == 1:
            resource = resources[0]
        else:
            m = Menu('Resources')
            for r in resources:
                item_args = args.copy()
                item_args['resource'] = r
                m.add_item(r.title(), command_name, args=item_args)
            return m.send(con)
    q = player.selected_units
    if isinstance(f, Feature):
        q = q.join(Unit.type).filter(getattr(UnitType, resource) == 1)
    elif isinstance(f, Building) and f.owner is not player:
        return player.message('You can only exploit your own buildings.')
    if not q.count():
        return player.message('You have no units capable of doing that.')
    for u in q:
        if u.home is None:
            u.speak('homeless')
        elif u.type.transport_capacity is not None:
            u.speak('no')
        else:
            u.speak('going')
            u.exploit(f, resource)


@command(location_type=LocationTypes.finalised)
def summon(player):
    """Summon all selected objects."""
    q = player.selected_units.join(Unit.type).filter(
        UnitType.transport_capacity.is_(None)
    )
    c = q.count()
    if not c:
        player.message('You have not selected any units.')
    else:
        for u in q:
            if u.coordinates == player.coordinates:
                u.speak('no')
                u.reset_action()
            else:
                u.speak('coming')
                u.travel(player.x, player.y)


@command(hotkey='h')
def health(player):
    """Show the health of the currently-selected unit, building, or feature."""
    fo = player.focussed_object
    if isinstance(fo, (Building, Unit)):
        player.message(f'{fo.hp} / {fo.max_hp} health.')
    elif isinstance(fo, Feature):
        player.message(fo.resources_string())


@command(hotkey='z')
def get_resources(player):
    """Show the resources for the currently-selected object. For land features,
    this is the same as checking h."""
    fo = player.focussed_object
    if fo is None:
        player.message('You must first focus something.')
    else:
        player.message(fo.resources_string('Nothing'))


@command(location_type=LocationTypes.finalised)
def build_building(location, player, id):
    """Build a building on the current map, using the given id as the type."""
    bt = BuildingType.get(id)
    fo = player.focussed_object
    if not isinstance(fo, Unit):
        player.message('You must first select a unit.')
    elif fo.owner is not player:
        fo.speak('no')
    elif bt.depends is not None and not Building.count(
        owner=player, location=location, type=bt.depends
    ):
        player.message(f'First build at least one {bt.depends.get_name()}.')
    elif bt not in fo.type.can_build:
        el = english_list(
            bt.builders, key=lambda thing: thing.get_name(), and_=' or'
        )
        player.message(f'{bt.get_name()} can only be built by {el}.')
    elif fo.home is None:
        fo.speak('homeless')
    else:
        home = fo.home
        d = bt.get_difference(home)
        if d:
            player.message(f'You require {difference_string(d)}.')
        else:
            home.take_requirements(bt)
            fo.speak('ok')
            b = location.add_building(bt, *fo.coordinates)
            b.set_owner(player)
            b.hp = 0
            b.save()
            player.message(f'{b.get_name()} ready.')


@command(location_type=LocationTypes.finalised)
def release(player):
    """Release a unit from the employ of this player."""
    fo = player.focussed_object
    if not isinstance(fo, Unit):
        player.message('You can only release units from your employ.')
    elif fo.owner is not player:
        player.message('You can only release your own units from employment.')
    elif fo.home is None:
        player.message('That unit has no home.')
    elif fo.coordinates != fo.home.coordinates:
        player.message(
            'That unit cannot be released from your employ until it is back '
            'home.'
        )
    else:
        bm = BuildingRecruit.first(unit_type_id=fo.type_id)
        for name in bm.resources:
            value = getattr(fo.home, name)
            value += getattr(bm, name)
            setattr(fo.home, name, value)
        fo.set_owner(None)
        fo.home = None
        fo.speak('bye')
        fo.save()
        player.message(f'You release {fo.get_name()} from your employ.')


@command(location_type=LocationTypes.finalised)
def repair(player, id):
    """Repair the building with the given ID."""
    b = Building.first(id=id, **player.same_coordinates())
    q = player.selected_units.join(Unit.type).filter(
        UnitType.transport_capacity.is_(None)
    )
    if b is None:
        player.message('No such building here.')
    elif b.hp >= b.max_hp:
        player.message(f'{b.get_name()} does not need repairing.')
    elif not q.count():
        player.message('You must select at least one unit capable of repairs.')
    else:
        for u in q:
            if u.coordinates == player.coordinates:
                u.speak('ok')
            else:
                u.speak('going')
            u.repair(b)
            u.save()


@command(location_type=LocationTypes.finalised)
def guard(player):
    """Set the currently-selected group of units to guard their current
    location."""
    q = player.selected_units.join(Unit.type).filter(
        UnitType.transport_capacity.is_(None)
    )
    if q.count():
        for u in q:
            u.speak('ok')
            u.guard()
    else:
        player.message('You must select at least one unit.')


@command(location_type=LocationTypes.finalised)
def patrol(player):
    """Set the currently-selected group of units to patrolling between their
    home, and the current coordinates."""
    q = player.selected_units.join(Unit.type).filter(
        UnitType.transport_capacity.is_(None)
    )
    if q.count():
        for u in q:
            u.speak('ok')
            u.patrol(*player.coordinates)
    else:
        player.message('You must select at least one unit.')


@command(location_type=LocationTypes.finalised)
def attack(player):
    """Destroy a building."""
    target = player.focussed_object
    if target is None or target.coordinates != player.coordinates:
        return player.message('Yu cannot see that here.')
    q = player.selected_units.filter_by(**player.same_coordinates()).join(
        Unit.type
    ).filter(UnitType.transport_capacity.is_(None))
    if q.count:
        attack = False
        for u in q:
            if u.type.attack_type is None:
                u.speak('dunno')
            elif u is target:
                u.speak('no')
            else:
                attack = True
                if isinstance(target, Building):
                    u.speak('destroy')
                elif isinstance(target, Unit):
                    u.speak('attack')
                else:
                    return player.message('Invalid object.')
                u.attack(target)
        if attack and target.owner not in (player, None):
            target.owner.sound('attack.wav')
            target.owner.message(
                f'Attack on {target.get_name()} at {target.coordinates}.'
            )
    else:
        player.message(
            'You must select at least one unit at your current coordinates.'
        )


@command(location_type=LocationTypes.finalised)
def move_entry_point(entry_point, player):
    """Move your entry point, so the home key will return you to these
    coordinates."""
    if entry_point is None:
        player.message('You do not have an entry point.')
    else:
        entry_point.coordinates = player.coordinates
        entry_point.save()
        player.message('Done.')


@command(location_type=LocationTypes.finalised)
def heal(player, unit_id):
    """Heal another unit."""
    target = Unit.first(**player.same_coordinates(), id=unit_id)
    if target is None:
        player.message('You canot see that here.')
    elif target.health is None:
        player.message(f'{target.get_name()} does not need healing.')
    else:
        q = player.selected_units.join(
            Unit.type
        ).filter(
            UnitType.transport_capacity.is_(None),
            UnitType.heal_amount.isnot(None)
        )
        if q.count():
            for u in q:
                u.speak('ok')
                u.heal_unit(target)
        else:
            player.message(
                'You must select at least one unit capable of healing.'
            )


@command(location_type=LocationTypes.finalised)
def steal(
    player, con, command_name, location, target_class_name=None, target_id=None
):
    """Instruct a unit to steal from another unit or building."""
    fo = player.focussed_object
    if not isinstance(fo, Unit):
        player.message('You must first select a unit.')
    elif fo.type.transport_capacity is not None:
        player.message(f'You cannot use {fo.get_name()} for stealing.')
    elif target_id is None:
        results = []
        for cls in (Unit, Building):
            results.extend(
                cls.all(
                    cls.owner_id.isnot(player.id), **player.same_coordinates()
                )
            )
        if results:
            m = Menu('Possible Targets')
            for r in results:
                cls = type(r)
                class_name = cls.__name__
                m.add_item(
                    r.get_name(), command_name, args=dict(
                        target_class_name=class_name, target_id=r.id
                    )
                )
            m.send(con)
        else:
            player.message('There is nothing here you can steal from.')
    else:
        cls = Base._decl_class_registry[target_class_name]
        target = cls.first(**player.same_coordinates(), id=target_id)
        if target is None:
            player.message('You cannot see that here.')
        else:
            a = fo.type.agility
            r = target.type.resistance
            percentage = ((100 / r) * a) / 100
            if random() > percentage:
                fo.speak('woops')
                for u in Unit.query(
                    Unit.owner_id.isnot(fo.owner_id), x=fo.x, y=fo.y,
                    location=location
                ).join(Unit.type).filter(UnitType.attack_type_id.isnot(None)):
                    u.attack(fo)
            else:
                resource_name = choice(target.resources)
                value = getattr(target, resource_name)
                if value:
                    setattr(target, resource_name, value - 1)
                    current = getattr(fo, resource_name)
                    setattr(fo, resource_name, current + 1)
                    fo.speak('ok')


@command(location_type=LocationTypes.finalised)
def embark(player):
    """Make a unit embark a transport."""
    fo = player.focussed_object
    if fo is None or fo.coordinates != player.coordinates or not isinstance(
        fo, Unit
    ) or fo.type.transport_capacity is None:
        player.message('Yu must first select a transport.')
    elif fo.transport is None:
        player.message('Yu must first file a flight plan.')
    elif len(fo.transport.passengers) >= fo.type.transport_capacity:
        player.message('That transport is already full.')
    else:
        for u in player.selected_units.filter_by(**player.same_coordinates()):
            fo.transport.add_passenger(u)
            if len(fo.transport.passengers) >= fo.type.transport_capacity:
                player.message(f'{fo.get_name()} is now full.')
                break
        else:
            player.message('Embarkation complete.')


@command(location_type=LocationTypes.finalised)
def disembark(con, command_name, player, unit_id=None):
    """Instruct a unit to disembark from the currently-focussed transport."""
    fo = player.focussed_object
    if fo is None or fo.coordinates != player.coordinates or not isinstance(
        fo, Unit
    ) or fo.type.transport_capacity is None:
        player.message('Yu must first select a transport.')
    elif fo.transport is None or not fo.transport.passengers:
        player.message(f'{fo.get_name()} has no passengers on board.')
    elif unit_id is None:
        m = Menu('Passengers')
        for p in fo.transport.passengers:
            m.add_item(p.get_name(), command_name, args=dict(unit_id=p.id))
        m.send(con)
    else:
        u = Unit.first(id=unit_id, onboard=fo.transport)
        if u is None:
            player.message('Invalid passenger.')
        else:
            fo.transport.remove_passenger(u)


@command(location_type=LocationTypes.finalised)
def launch(player):
    """Launch the currently-selected transport."""
    fo = player.focussed_object
    if fo is None or fo.coordinates != player.coordinates or not isinstance(
        fo, Unit
    ) or fo.type.transport_capacity is None:
        player.message('Yu must first select a transport.')
    elif fo.transport is None:
        player.message('You must first file a flight plan.')
    elif fo.coordinates == fo.transport.destination.coordinates:
        fo.speak('no')
    else:
        fo.transport.launch()
        player.focussed_object is None


@command(location_type=LocationTypes.finalised)
def set_destination(con, command_name, location, player, building_id=None):
    """Set the destination for the currently-focussed transport."""
    q = Building.query(location=location).join(Building.type).filter(
        BuildingType.landing_field.is_(True)
    )
    fo = player.focussed_object
    if fo is None or fo.coordinates != player.coordinates or not isinstance(
        fo, Unit
    ) or fo.type.transport_capacity is None:
        player.message('Yu must first select a transport.')
    elif building_id is None:
        if q.count():
            m = Menu('Landing Sites')
            for b in q:
                m.add_item(
                    b.get_name(), command_name, args=dict(building_id=b.id)
                )
            m.send(con)
        else:
            player.message('You must first build a landing site.')
    else:
        b = q.filter(Building.id == building_id).first()
        if b is None:
            player.message('Invalid landing site.')
        else:
            if fo.transport is None:
                fo.set_transport(b).save()
            else:
                fo.transport.destination = b
                fo.transport.save()
            player.message(f'Flight plan to {b.get_name()} filed.')


@command(hotkey='v')
def view_objects(player):
    """View the objects at your current coordinates."""
    el = english_list(
        player.visible_objects, key=lambda obj: obj.get_name(),
        empty='nothing'
    )
    player.message(f'You can see: {el}.')

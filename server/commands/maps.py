"""Provides map-related commands."""

from .commands import command, LocationTypes

from ..db import (
    Building, BuildingMobile, BuildingType, EntryPoint, Feature, FeatureType,
    Map, Mobile, MobileType, Player, Base
)
from ..menus import Menu, YesNoMenu
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
    for t in BuildingType.query().order_by(
        BuildingType.homely.desc(), BuildingType.name
    ):
        if t.homely:
            name = f'{t.name} (*)'
        else:
            name = t.name
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
    player.message(obj.get_name())
    if isinstance(obj, Mobile):
        player.deselect_mobiles()
        obj.selected = True
        obj.save()


@command(hotkey='[')
def previous_object(player):
    """Select the previous object."""
    switch_object(player, -1)


@command(hotkey=']')
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


@command(location_type=LocationTypes.map, hotkey='s')
def stats(player, location):
    """Show resources for this map."""
    d = {}
    for f in location.features:
        for name in f.type.resources:
            if name not in d:
                d[name] = 0
            d[name] += getattr(f, name)
    for name in sorted(d):
        player.message(f'{name.title()}: {d[name]}')


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


@command(location_type=LocationTypes.map)
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
        m.add_item('Create Random Map', 'random_map')
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
                    'How many of that feature type do you want?', command_name,
                    argument_name='value', args=args
                )
            else:
                try:
                    value = int(value)
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
            BuildingType.homely.is_(True)
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


def select_mobiles(index, player):
    """Select a group of mobiles."""
    player.deselect_mobiles()
    if not index:
        group = 'All'
        q = Mobile.query(owner=player)
    else:
        try:
            q = MobileType.all()
            t = q[index - 1]
            group = t.name
            q = Mobile.query(owner=player, type=t)
        except IndexError:
            c = len(q)
            if c:
                player.message(
                    f'There are only {c} {pluralise(c, "type")} of unit.'
                )
            else:
                player.message('There is nothing here.')
            return
    c = q.update({Mobile.selected: True})
    player.message(f'{group}: {c} {pluralise(c, "unit")} selected.')


def select_mobile_list(index, player):
    """Select a mobile from a list grouped by types."""
    if not index:
        name = 'All Units'
        kwargs = {}
    else:
        types = MobileType.all()
        try:
            type = types[index - 1]
            kwargs = dict(type=type)
            name = f'{type.name} Units'
        except IndexError:
            c = len(types)
            return player.message(
                f'There are only {c} {pluralise(c, "type")} of unit.'
            )
    q = Mobile.query(location=player.location, owner=player, **kwargs)
    c = q.count()
    if c:
        m = Menu(name)
        m.add_label(f'Units: {c}')
        for u in q:
            m.add_item(
                f'{u.get_name()} {u.coordinates}', 'select_mobile',
                args=dict(id=u.id)
            )
            m.send(player.connection)
    else:
        player.message('No units to show.')


for x, hotkey in enumerate('aqwertyuiop'):
    if hotkey == 'a':
        description = 'Select all your mobiles.'
    else:
        description = 'Select a group of mobiles.'
    command(
        name=f'select_mobiles_{hotkey}', description=description, hotkey=hotkey
    )(
        lambda player, index=x: select_mobiles(index, player)
    )
    command(
        name=f'select_mobile_list_{hotkey}',
        description='Select a single mobile from a list.',
        hotkey=f'shift+{hotkey}'
    )(
        lambda player, index=x: select_mobile_list(index, player)
    )


@command()
def select_mobile(location, player, id):
    """Select a unit by its id."""
    player.deselect_mobiles()
    u = Mobile.first(owner=player, location=location, id=id)
    if u is None:
        player.message('That unit does not exist.')
    else:
        u.selected = True
        u.save()
        player.message(f'{u.get_name()} selected.')


@command(hotkey='x')
def toggle_select_mobile(player):
    """Select r deselect a mobile."""
    fo = player.focussed_object
    if not isinstance(fo, Mobile):
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


@command(hotkey=' ')
def activate(player, con):
    """Show the activation menu for the currently focussed object."""
    m = Menu('Object Menu')
    fo = player.focussed_object
    if fo is not None:
        m.add_label(fo.get_name())
        if isinstance(fo, (Building, Mobile)):
            m.add_label(f'{fo.hp} / {fo.max_hp} health')
            if fo.owner is None:
                m.add_item('Acquire', 'acquire', args={'id': fo.id})
        if isinstance(fo, Building) and fo.owner is player:
            for name in BuildingType.resource_names():
                value = getattr(fo, name)
                m.add_label(f'{name.title()}: {value}')
            if fo.type.homely:
                m.add_item('Set Home', 'set_home', args={'id': fo.id})
                for bm in BuildingMobile.query(
                    BuildingMobile.building_type_id.in_(
                        [b.type.id for b in player.owned_buildings]
                    )
                ):
                    t = MobileType.get(bm.building_type_id)
                    m.add_item(
                        f'Recruit {t} (requires {bm.resources_string()}',
                        'recruit', args=dict(building=fo.id, mobile=t.id)
                    )
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
    m.add_item('Summon', 'summon')
    for t in BuildingType.all():
        m.add_item(
            f'Build {t.name} (requires {t.resources_string("nothing")}',
            'build_building', args=dict(id=t.id)
        )
    m.send(con)


@command(location_type=LocationTypes.finalised)
def acquire(player, id):
    """Acquire the currently-focussed object."""
    fo = player.focussed_object
    if fo is None:
        player.message('You must focus an object first.')
    if fo.x != player.x and fo.y != player.y:
        player.message(
            'You can only acquire objects at your current coordinates.'
        )
    elif fo.owner is not None:
        player.message('That object has already been acquired.')
    else:
        fo.owner = player
        player.message('Done.')


def _recruit(building_id, building_mobile_id):
    """Actually perform the recruiting."""
    b = Building.get(building_id)
    if b is None:
        return  # It has since been destroyed.
    bm = BuildingMobile.get(building_mobile_id)
    t = MobileType.get(bm.mobile_type_id)
    m = b.location.add_mobile(t, *b.coordinates)
    player = b.owner
    m.owner = player
    m.home = b
    m.save()
    player.message(f'{m.get_name()} ready.')


@command(location_type=LocationTypes.finalised)
def recruit(player, location, building, mobile):
    """Recruit a mobile."""
    b = player.focussed_object
    m = MobileType.get(mobile)
    if not isinstance(b, Building):
        player.message('You must select a building.')
    elif not b.type.homely:
        player.message('Only home buildings can be used for recruitment.')
    elif m is None:
        player.message('Invalid recruitment.')
    else:
        types = []
        for bm in BuildingMobile.all(mobile_type_id=m.id):
            t = BuildingType.get(bm.building_type_id)
            if Building.count(owner=player, location=location, type=t):
                break  # They can build.
        else:
            return player.message(f'Requires {english_list(types)}.')
        d = bm.get_difference(b)
        if d:
            player.message(f'You require {difference_string(d)}.')
        else:
            b.take_requirements(bm)
            player.call_later(bm.pop_time, _recruit, b.id, bm.id)


@command()
def set_home(player, id):
    """Set the home of all selected mobiles."""
    q = player.selected_mobiles
    b = Building.get(id)
    if b is None or b.owner is not player:
        player.message('Invalid building.')
    elif not b.type.homely:
        player.message('That building cannot be used as a home.')
    else:
        c = q.update({Mobile.home_id: id})
        player.message(f'Updated {c} {pluralise(c, "home")}.')


@command()
def exploit(con, args, command_name, player, class_name, id, resource=None):
    """Exploit a feature."""
    cls = Base._decl_class_registry[class_name]
    f = cls.first(id=id, **player.same_coordinates())
    if f is None:
        player.message('You cannot see that here.')
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
    q = player.selected_mobiles.join(
        Mobile.type
    ).filter(getattr(MobileType, resource) == 1)
    if not q.count():
        return player.message('You have no units capable of doing that.')
    for m in q:
        if m.home is None:
            player.message(
                f'{m.get_name()} has no home to bring resources back to.'
            )
        else:
            player.message(f'Dispatching {m.get_name()}.')
            m.exploit(f, resource)


@command()
def summon(player):
    """Summon all selected objects."""
    q = player.selected_mobiles
    c = q.count()
    if not c:
        player.message('You have not selected any mobiles.')
    else:
        for m in q:
            m.travel(player.x, player.y)
        el = english_list(q, key=lambda o: o.get_name())
        player.message(f'You summon {el}.')


@command(hotkey='h')
def health(player):
    """Show the health of the currently-selected unit, building, or feature."""
    fo = player.focussed_object
    if isinstance(fo, (Building, Mobile)):
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
    t = BuildingType.get(id)
    if t.depends is not None and not Building.count(
        owner=player, location=location, type=t.depends
    ):
        return player.message(f'{t.name} requires {t.depends.name}.')
    for m in player.selected_mobiles.filter_by(**player.same_coordinates()):
        if m.type in t.builders:
            obj = m
            break
    else:
        return player.message(
            'First select and summon a unit capable of building this building.'
        )
    home = obj.home
    if home is None:
        return player.message(f'{obj.get_name()} has no home.')
    d = t.get_difference(home)
    if d:
        return player.message(f'You require {difference_string(d)}.')
    home.take_requirements(t)
    b = location.add_building(t, *player.coordinates)
    b.owner = player
    b.hp = 1
    b.save()
    player.message(f'{b.get_name()} ready.')

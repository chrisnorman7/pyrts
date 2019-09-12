"""Provides map-related commands."""

from twisted.internet import reactor

from .commands import command, LocationTypes

from ..db import (
    Building, BuildingMobile, BuildingType, EntryPoint, Feature, FeatureType,
    Map, Mobile, MobileType, Player
)
from ..menus import Menu, YesNoMenu
from ..util import pluralise, is_are


@command(location_type=LocationTypes.not_map)
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


@command(location_type=LocationTypes.template, hotkey='b')
def build(con, location):
    """Add something to a map in edit mode."""
    m = Menu('Build', dismissable=True)
    m.add_label('General')
    m.add_item('Entry Point', 'add_entry_point')
    m.add_label('Buildings')
    for t in BuildingType.alphabetized():
        if t.homely:
            name = f'{t.name} (*)'
        else:
            name = t.name
        m.add_item(name, 'add_building', args={'id': t.id})
    m.add_label('Land Features')
    for t in FeatureType.alphabetized():
        m.add_item(t.name, 'add_feature', args={'id': t.id})
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
def add_building(player, location, con, command_name, id=None):
    """Add a building."""
    if id is None:
        m = Menu('Buildings')
        for t in BuildingType.alphabetized():
            m.add_item(t.name, command_name, args={'id': t.id})
        m.send(con)
    else:
        type = BuildingType.get(id)
        if type is None:
            return player.message('Invalid ID.')
        b = location.add_building(type, player.x, player.y)
        b.save()
        player.message(f'{type.name} created.')


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
    objects = player.visible_objects
    c = len(objects)
    if not c:
        return player.message('There are no objects at these coordinates.')
    player.focus += direction
    if player.focus < 0:
        player.focus = c - 1
    elif player.focus >= c:
        player.focus = 0
    player.save()
    fo = player.focussed_object
    player.message(fo.get_name())
    if isinstance(fo, Mobile):
        fo.selected = True
        fo.save()


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
        player.join_map(m)


def focus_object(hotkey, player):
    """Focus a specific object."""
    if hotkey == 0:
        return switch_object(player, 0)
    q = player.visible_objects
    c = len(q)
    if c < hotkey:
        player.message(f'There {is_are(c)} only {c} {pluralise(c, "object")}.')
    else:
        player.focus = hotkey
        switch_object(player, -1)


for x in range(10):
    if not x:
        description = 'Show the currently-focused object.'
    else:
        description = f'Select object {x}.'
    command(
        name=f'select_object_{x}', description=description, hotkey=str(x)
    )(lambda player, index=x: focus_object(index, player))


def select_mobile(index, player):
    """Select a group of mobiles."""
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
            player.message(
                f'There are only {c} {pluralise(c, "type")} of mobile.'
            )
            return
    c = q.update({Mobile.selected: True})
    player.message(f'{group}: {c} {pluralise(c, "unit")} selected.')


for x, hotkey in enumerate('aqwertyuiop'):
    if hotkey == 'a':
        description = 'Select all your mobiles.'
    else:
        description = 'Select a group of mobiles.'
    command(
        name=f'select_mobile_{hotkey}', description=description, hotkey=hotkey
    )(
        lambda player, index=x: select_mobile(index, player)
    )


@command(hotkey=' ')
def activate(player, con):
    """Show the activation menu for the currently focussed object."""
    fo = player.focussed_object
    m = Menu('Object Menu')
    m.add_label(str(fo))
    if isinstance(fo, (Building, Mobile)) and fo.owner is None:
        m.add_item('Acquire', 'acquire', args={'id': fo.id})
    if isinstance(fo, Building) and fo.owner is player:
        for bm in BuildingMobile.all(building_type_id=fo.type_id):
            t = MobileType.get(bm.mobile_type_id)
            m.add_item(
                f'Recruit {t} ({bm.resources_string()}', 'recruit',
                args={'building': fo.id, 'building_mobile': bm.id}
            )
        m.add_item('Set Home', 'set_home', args={'id': fo.id})
    if isinstance(fo, Player):
        if player.admin:
            if fo.admin:
                m.add_item('Revoke Admin', 'revoke_admin', args={'id': fo.id})
            else:
                m.add_item('Make Admin', 'make_admin', args={'id': fo.id})
            if fo.connected:
                m.add_item('Disconnect', 'disconnect', args={'id': fo.id})
            m.add_item('Delete', 'delete_player', args={'id': fo.id})
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


def _recruit(player_id, building_id, building_mobile_id):
    """Actually perform the recruiting."""
    b = Building.get(building_id)
    if b is None:
        return  # It has since been destroyed.
    bm = BuildingMobile.get(building_mobile_id)
    t = MobileType.get(bm.mobile_type_id)
    m = b.location.add_mobile(t, b.x, b.y)
    player = Player.get(player_id)
    m.owner = player
    m.home = b
    m.save()
    player.message(f'{m.get_name()} ready.')


@command(location_type=LocationTypes.finalised)
def recruit(player, building, building_mobile):
    """Recruit a mobile."""
    b = Building.get(building)
    if building is None or b.x != player.x or b.y != player.y:
        player.message(
            'You can only recruit using buildings at your current location.'
        )
    else:
        bm = BuildingMobile.get(building_mobile)
        if bm is None:
            player.message('Invalid recruitment.')
        else:
            take = {}
            for name in BuildingMobile.resource_names():
                requires = getattr(bm, name)
                value = getattr(b, name)
                if requires is not None:
                    take[name] = requires
                    if value < requires:
                        player.message(
                            f'You are short {requires - value} {name}.'
                        )
                        return
            else:
                for name, value in take.items():
                    setattr(b, name, getattr(b, name) - value)
                pt = bm.pop_time
                reactor.callLater(pt, _recruit, player.id, b.id, bm.id)
                player.message(f'({pt} {pluralise(pt, "second")})')

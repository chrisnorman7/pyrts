from pytest import raises

from datetime import datetime

from server.db import (
    Building, BuildingBuilder, BuildingType, EntryPoint, Feature, FeatureType,
    Map, Unit, Player, Base
)
from server.db.units import UnitActions
from server.db.util import dump_object
from server.exc import InvalidUsername, InvalidPassword, NoSuchSound


def test_map(map):
    assert isinstance(map, Map)
    map.save()
    assert map.size_x == 25
    assert map.size_y == 25
    assert map.features == []


def test_finalise(map):
    assert map.finalised is None
    map.finalise()
    assert isinstance(map.finalised, datetime)


def test_building(player, farm, map):
    player.location = map
    player.save()
    b = map.add_building(farm, 0, 0)
    assert isinstance(b, Building)
    b.save()
    assert b.owner is None
    assert b.type is farm
    assert b.location is map
    assert b.x == 0
    assert b.y == 0
    assert b.get_full_name() == f'{b.get_name()} (Unclaimed)'
    b.owner = player
    b.save()
    assert b.owner_id == player.id
    assert b.get_full_name() == f"{b.type.name} 1 ({player.name})"
    assert b in map.buildings


def test_unit(peasant, player, map):
    m = map.add_unit(peasant, x=1, y=2)
    assert m.type is peasant
    assert isinstance(m, Unit)
    assert m.x == 1
    assert m.y == 2
    assert m.gold == 0
    assert m.wood == 0
    assert m.food == 0
    assert m.water == 0
    assert m.stone == 0
    assert m.owner is None
    assert m.get_full_name() == f'{m.get_name()} [Unemployed]'
    m.owner = player
    m.save()
    assert m.owner_id == player.id
    assert m.get_full_name() == f'{peasant.name} 1 [employed by {player.name}]'
    assert m in map.units


def test_feature(map, mine):
    f = map.add_feature(mine, 4, 5)
    assert isinstance(f, Feature)
    assert f.type is mine
    assert f.x == 4
    assert f.y == 5
    assert f.get_full_name() == f'{f.get_name()} [0 gold]'
    f.gold = 0
    assert f.get_full_name() == f'{f.get_name()} [0 gold]'
    f.gold = 95
    assert f.get_full_name() == f'{f.get_name()} [95 gold]'
    assert f in map.features


def test_player_create():
    username = 'username'
    password = 'password'
    name = 'This player is a test'
    p = Player.create(username, password, name)
    p.save()
    assert p.username == username
    assert p.name == name
    assert p.check_password(password) is True


def test_player_authenticate(password, player):
    assert Player.authenticate(player.username, password) is player
    with raises(InvalidUsername):
        Player.authenticate('Not a username', 'Not a password.')
    with raises(InvalidPassword):
        Player.authenticate(player.username, 'Invalid Password.')


def test_player_check_password(password, player):
    assert player.check_password(password) is True
    assert player.check_password('Wrong') is False


def test_player_set_password():
    p = Player.create('test player', 'some password', 'test name')
    p.set_password('new')
    assert p.check_password('new') is True


def test_player_location(player, map):
    player.location_id = None
    player.save()
    assert player.location is None
    assert map.players == []
    player.location = map
    assert map.players == [player]


def test_dump_object(mine, map):
    f = map.add_feature(mine, 0, 0)
    f.save()
    d = dump_object(f)
    assert d['id'] == f.id


def test_player_neighbours(player, map):
    player.location = map
    player.save()
    assert player.neighbours.all() == []
    player_2 = Player.create('username', 'password', 'proper name')
    player_2.location = map
    player_2.save()
    assert player.neighbours.all() == [player_2]
    assert player_2.neighbours.all() == [player]


def test_map_ownership(player):
    m = Map(name='Test Ownership', owner=player)
    m.save()


def test_map_copy(farm, mine, peasant, map):
    b = map.add_building(farm, 0, 0)
    m = map.add_feature(mine, 1, 1)
    m.gold = 1234
    p = map.add_unit(peasant, 2, 2)
    p.home = b
    for thing in (b, m, p):
        thing.save()
    m = map.copy()
    assert m.id is None
    m.save()
    assert m.id is not None
    assert m.id != map.id
    assert m.name == map.name
    assert m.buildings[0].id is not None
    assert m.buildings[0].type is farm
    assert m.features[0].id is not None
    assert m.features[0].type is mine
    assert m.features[0].gold == 1234
    assert m.units[0].id is not None
    assert m.units[0].type is peasant
    assert m.units[0].home is m.buildings[0]


def test_building_recruits(farm, peasant):
    assert farm not in peasant.recruiters
    assert peasant not in farm.recruits
    assert farm not in peasant.recruiters
    farm.recruits.append(peasant)
    assert peasant in farm.recruits
    assert farm in peasant.recruiters


def test_get_pop_time(farm, peasant):
    assert peasant in farm.recruits, 'Tests ran out of order.'
    assert farm.get_pop_time(peasant) == 4


def test_set_pop_time(peasant, farm):
    assert peasant in farm.recruits, 'Tests ran out of order.'
    value = 5432
    farm.set_pop_time(peasant, value)
    assert farm.get_pop_time(peasant) == value


def test_depends(farm):
    house = BuildingType(name='House', depends=farm)
    house.save()
    assert house.depends is farm
    assert house in farm.dependencies


def test_builders(farm, peasant):
    assert farm in peasant.can_build
    assert peasant in farm.builders
    farm.builders.append(peasant)
    assert peasant in farm.builders
    assert farm in peasant.can_build


def test_resources(mine, quarry):
    assert mine.resources == ['gold']
    assert quarry.resources == ['stone']
    m = FeatureType(name='Jungle', food=1, water=1, wood=1)
    m.save()
    assert m.resources == ['food', 'water', 'wood']


def test_valid_coordinates(map):
    assert map.valid_coordinates(0, 0)
    assert map.valid_coordinates(3, 5)
    assert map.valid_coordinates(map.size_x, map.size_y)
    assert not map.valid_coordinates(-1, -1)
    assert not map.valid_coordinates(map.size_x + 1, map.size_y + 1)


def test_entry_points(map):
    e = map.add_entry_point(1, 2)
    e.save()
    m = map.copy()
    m.save()
    p = m.entry_points[0]
    assert p.x == e.x
    assert p.y == e.y
    assert p.occupant is None


def test_map_delete(map, player, farm, mine, peasant):
    assert map.id is not None
    player.location = map
    player.save()
    e = map.add_entry_point(1, 2)
    e.save()
    b = map.add_building(farm, 0, 0)
    b.save()
    m = map.add_feature(mine, 10, 10)
    m.save()
    p = map.add_unit(peasant, 15, 15)
    p.save()
    with raises(AssertionError):
        map.delete()
    player.location = None
    player.save()
    map.delete()
    assert EntryPoint.first(id=e.id) is None
    assert Building.first(id=b.id) is None
    assert Feature.first(id=m.id) is None
    assert Unit.first(id=p.id) is None
    assert Map.first(id=map.id) is None


def test_random_map(mine, quarry):
    name = 'Test Random Map'
    players = 4
    min_resource = 7
    max_resource = 8
    features = {mine: 5, quarry: 10}
    m = Map.create_random(name, players, min_resource, max_resource, features)
    assert m.id is not None
    assert len(m.features) == 15
    assert len(m.entry_points) == 4
    assert len(m.units) == 0
    resulting_features = {mine: 0, quarry: 0}
    for f in m.features:
        resulting_features[f.type] += 1
        for name in f.type.resources:
            value = getattr(f, name)
            if value not in (7, 8):
                raise AssertionError(repr(f))
    assert resulting_features[mine] == features[mine]
    assert resulting_features[quarry] == features[quarry]


def test_sound(mine):
    assert isinstance(mine.sound, str)
    f = FeatureType(name='Nothing really')
    with raises(NoSuchSound):
        f.sound


def test_player_delete(player, map, farm):
    f = map.add_building(farm, 0, 0)
    f.owner = player
    map.location = map
    f.location = map
    for thing in (map, player, f):
        thing.save()
    player.delete()
    assert f.owner_id is None


def test_exploiting(map, mine, peasant, farm):
    p = map.add_unit(peasant, 0, 0)
    f = map.add_building(farm, 0, 0)
    p.exploiting = f
    assert p.exploiting_class == 'Building'
    assert p.exploiting_id == f.id
    m = map.add_feature(mine, 0, 0)
    p.exploiting = m
    assert p.exploiting_class == 'Feature'
    assert p.exploiting_id == m.id
    p.exploiting = None
    assert p.exploiting_class is None
    assert p.exploiting_id is None


def test_coordinates(player):
    assert player.coordinates == (0, 0)
    player.coordinates = (1, 2)
    assert player.coordinates == (1, 2)


def test_target(map, peasant):
    p = map.add_unit(peasant, 0, 0)
    p.save()
    assert p.target == (0, 0)
    p.target = (4, 4)
    assert p.target == (4, 4)


def test_exploit(player, map, peasant, mine, farm):
    f = map.add_building(farm, 0, 0)
    p = map.add_unit(peasant, 0, 0)
    p.owner = player
    p.home = f
    m = map.add_feature(mine, 2, 1)
    m.gold = 5
    for thing in (f, m, p):
        thing.save()

    def check_peasant():
        assert p.home is f
        assert p.exploiting is m
        assert p.target == m.coordinates

    p.exploit(m, 'gold')
    check_peasant()
    assert p.coordinates == (0, 0)
    assert p.action is UnitActions.exploit
    Unit.progress(p.id)
    check_peasant()
    assert p.coordinates == (1, 1)
    assert p.action == UnitActions.exploit
    Unit.progress(p.id)
    check_peasant()
    assert p.coordinates == m.coordinates
    assert p.action == UnitActions.exploit
    Unit.progress(p.id)
    check_peasant()
    assert m.gold == 4
    assert p.action is UnitActions.drop
    assert p.coordinates == m.coordinates
    Unit.progress(p.id)
    check_peasant()
    assert p.coordinates == (1, 0)
    assert p.action is UnitActions.drop
    Unit.progress(p.id)
    check_peasant()
    assert f.gold == 0
    assert p.coordinates == (0, 0)
    Unit.progress(p.id)
    check_peasant()
    assert p.action is UnitActions.exploit
    assert f.gold == 1
    assert p.coordinates == f.coordinates
    Unit.progress(p.id)
    assert p.action is UnitActions.exploit
    check_peasant()
    assert p.coordinates == (1, 1)


def test_health(farm, map):
    b = map.add_building(farm, 0, 0)
    b.save()
    assert b.max_hp == farm.max_health
    assert b.hp == b.max_hp
    value = b.max_hp * 2
    b.hp = value
    assert b.health == value
    b.heal(value)
    assert b.hp == b.max_hp
    assert b.health is None


def test_focussed_object(farm, peasant, mine, player, map):
    b = map.add_building(farm, 0, 0)
    m = map.add_feature(mine, 0, 0)
    p = map.add_unit(peasant, 0, 0)
    for thing in (b, m, p):
        thing.save()
    player.location = map
    assert player.focussed_class is None
    assert player.focussed_id is None
    assert player.focussed_object is None
    player.focussed_object = b
    assert player.focussed_class == 'Building'
    assert player.focussed_id == b.id
    assert player.focussed_object is b
    player.focussed_object = m
    assert player.focussed_class == 'Feature'
    assert player.focussed_id == m.id
    assert player.focussed_object is m
    player.focussed_object = p
    assert player.focussed_class == 'Unit'
    assert player.focussed_id == p.id
    assert player.focussed_object is p
    player.focussed_object = None
    assert player.focussed_class is None
    assert player.focussed_id is None
    assert player.focussed_object is None


def test_visible_objects(player, farm, mine, peasant, map):
    player.location = map
    assert player.visible_objects == []
    b = map.add_building(farm, *player.coordinates)
    assert player.visible_objects == [b]
    m = map.add_feature(mine, *player.coordinates)
    assert player.visible_objects == [b, m]
    p = map.add_unit(peasant, *player.coordinates)
    assert player.visible_objects == [b, m, p]
    player.coordinates = (1, 1)
    assert player.visible_objects == []


def test_builder(peasant):
    castle = BuildingType(name='Castle')
    castle.save()
    bb = peasant.add_building(castle)
    assert isinstance(bb, BuildingBuilder)
    assert bb.building_type_id == castle.id
    assert bb.unit_type_id == peasant.id
    bb.save()
    assert peasant.get_building(castle) is bb
    assert castle in peasant.can_build
    assert peasant in castle.builders


def test_check_difference(peasant):
    c = BuildingType(name='Castle', gold=1, water=2, stone=3)
    c.save()
    bm = c.add_recruit(peasant, gold=1, water=1, stone=1)
    bm.save()
    d = c.get_difference(bm)
    assert d == dict(water=1, stone=2)


def test_resources_dict(map, farm):
    b = map.add_building(farm, 0, 0)
    b.save()
    d = b.resources_dict()
    assert d == dict(wood=0, gold=0, food=0, water=0, stone=0)


def test_distance_to(map, farm, peasant):
    b = map.add_building(farm, 0, 0)
    p = map.add_unit(peasant, 1, 1)
    assert b.distance_to(p) == 1
    p.coordinates = (3, 3)
    assert b.distance_to(p) == 3
    p.coordinates = (5, 4)
    assert b.distance_to(p) == 5


def test_directions_to(map, farm, peasant):
    b = map.add_building(farm, 0, 0)
    p = map.add_unit(peasant, 1, 1)
    assert b.directions_to(p) == '1 north, 1 east'
    p.coordinates = (0, 0)
    assert b.directions_to(p) == 'here'
    p.coordinates = (2, 3)
    assert b.directions_to(p) == '3 north, 2 east'
    assert p.directions_to(b) == '3 south, 2 west'


def test_class_from_table():
    assert Base.get_class_from_table(FeatureType.__table__) is FeatureType
    assert Base.get_class_from_table(Player.__table__) is Player


def test_exploit_multiple(map, player, farm, mine, peasant, quarry):
    b = map.add_building(farm, 0, 0)
    b.owner = player
    m = map.add_feature(mine, 0, 0)
    m.gold = 100
    q = map.add_feature(quarry, 0, 0)
    q.stone = 100

    u = map.add_unit(peasant, 0, 0)
    u.owner = player
    u.home = b
    for thing in (b, m, q, u):
        thing.save()
    u.exploit(m, 'gold')
    Unit.progress(u.id)
    assert u.gold == 1
    u.exploit(q, 'stone')
    assert u.gold == 1
    Unit.progress(u.id)
    assert u.gold == 1
    assert u.stone == 1
    Unit.progress(u.id)
    assert b.gold == 1
    assert b.stone == 1
    assert u.gold == 0
    assert u.stone == 0


def test_owned_units_order(player, map, peasant, farmer):
    player.location = map
    for cls in (Unit, Building):
        cls.query(cls.owner_id.isnot(None)).update({cls.owner_id: None})
    p1 = map.add_unit(peasant, 0, 0)
    f = map.add_unit(farmer, 0, 0)
    p2 = map.add_unit(peasant, 0, 0)
    for thing in (p1, f, p2):
        thing.owner = player
        thing.save()
    q = Unit.query(
        owner=player
    ).order_by(Unit.updated).all()
    assert player.owned_units == q
    assert player.owned_units == [p1, f, p2]
    p1.owner = None
    p1.save()
    p1.owner = player
    p1.save()  # Trigger p1.updated to be modified.
    q = Unit.query(owner=player).order_by(
        Unit.updated
    ).all()
    assert q == [f, p2, p1]
    assert player.owned_units == [f, p2, p1]


def test_unit_types(map, player, peasant, farmer):
    player.location = map
    player.save()
    for cls in (Unit, Building):
        cls.query(cls.owner_id.isnot(None)).update({cls.owner_id: None})
    assert not player.owned_buildings
    assert not player.owned_units
    p = map.add_unit(peasant, 0, 0)
    f = map.add_unit(farmer, 0, 0)
    for thing in (p, f):
        thing.owner = player
        thing.save()
    assert player.owned_units == [p, f]
    assert player.unit_types == [peasant, farmer]
    p.owner = None
    p.save()
    assert player.unit_types == [farmer]
    p.owner = player
    p.save()
    assert player.owned_units == [f, p]
    assert player.unit_types == [farmer, peasant]
    f2 = map.add_unit(farmer, 0, 0)
    f2.owner = player
    f2.save()
    assert player.owned_units == [f, p, f2]
    assert player.unit_types == [farmer, peasant]

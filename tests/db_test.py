from pytest import raises

from datetime import datetime

from server.db import (
    Building, BuildingType, EntryPoint, Feature, FeatureType, Map, Mobile,
    Player
)
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
    assert b.get_full_name() == f'{b.type.name} (Unclaimed)'
    b.owner = player
    b.save()
    assert b.owner_id == player.id
    assert b.get_full_name() == f"{b.type.name} 1 ({player.name})"
    assert b in map.buildings


def test_mobile(peasant, player, map):
    m = map.add_mobile(peasant, x=1, y=2)
    assert m.type is peasant
    assert isinstance(m, Mobile)
    assert m.x == 1
    assert m.y == 2
    assert m.owner is None
    assert m.get_full_name() == f'{peasant.name} [Unemployed]'
    m.owner = player
    m.save()
    assert m.owner_id == player.id
    assert m.get_full_name() == f'{peasant.name} 1 [employed by {player.name}]'
    assert m in map.mobiles


def test_feature(map, mine):
    f = map.add_feature(mine, 4, 5)
    assert isinstance(f, Feature)
    assert f.type is mine
    assert f.x == 4
    assert f.y == 5
    assert f.get_full_name() == f'{mine.name} [0 gold]'
    f.gold = 0
    assert f.get_full_name() == f'{mine.name} [0 gold]'
    f.gold = 95
    assert f.get_full_name() == f'{mine.name} [95 gold]'
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
    p = map.add_mobile(peasant, 2, 2)
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
    assert m.mobiles[0].id is not None
    assert m.mobiles[0].type is peasant
    assert m.mobiles[0].home is m.buildings[0]


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
    assert farm not in peasant.can_build
    assert peasant not in farm.builders
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
    p = map.add_mobile(peasant, 15, 15)
    p.save()
    with raises(AssertionError):
        map.delete()
    player.location = None
    player.save()
    map.delete()
    assert EntryPoint.first(id=e.id) is None
    assert Building.first(id=b.id) is None
    assert Feature.first(id=m.id) is None
    assert Mobile.first(id=p.id) is None
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
    assert len(m.mobiles) == 0
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


def test_exploit(map, mine, peasant, farm):
    p = map.add_mobile(peasant, 0, 0)
    f = map.add_building(farm, 0, 0)
    p.exploiting = f
    assert p.exploiting_class == 'Building'
    assert p.exploiting_id == f.id
    m = map.add_feature(mine, 0, 0)
    p.exploiting = m
    assert p.exploiting_class == 'Feature'
    assert p.exploiting_id == m.id


def test_coordinates(player):
    assert player.coordinates == (0, 0)
    player.coordinates = (1, 2)
    assert player.coordinates == (1, 2)


def test_target(map, peasant):
    p = map.add_mobile(peasant, 0, 0)
    p.save()
    assert p.target == (None, None)
    p.target = (0, 0)
    assert p.target == (0, 0)

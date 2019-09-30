from pytest import fixture

from server.db import (
    BuildingType, FeatureType, Map, UnitType, Player, setup
)
from server.events import register, unregister, events, on_exploit, on_drop
from server.options import options

password = 'TestsAreFun123'
farm = 'Farm'
peasant = 'Peasant'
farmer = 'Farmer'
mine = 'Mine'
quarry = 'Quarry'


@fixture(scope='session', autouse=True)
def create_stuff():
    """Initialise the database and create stuff."""
    events.clear()
    setup()
    ut = UnitType.first(name=peasant)
    ut.stone = 1
    assert options.start_building is not None
    Player.create('test', password, 'Test Player').save()


@fixture(name='map')
def new_map():
    """Return a Map instance."""
    m = Map(name='Test Map')
    m.save()
    return m


@fixture(name='password')
def get_password():
    return password


@fixture(name='player')
def new_player(password):
    return Player.first()


@fixture(name='farm')
def get_farm():
    """Get the farm building type."""
    return BuildingType.one(name=farm)


@fixture(name='peasant')
def get_peasant():
    """Get the peasant unit type."""
    return UnitType.one(name=peasant)


@fixture(name='farmer')
def get_farmer():
    return UnitType.one(name=farmer)


@fixture(name='mine')
def get_mine():
    return FeatureType.one(name=mine)


@fixture(name='quarry')
def get_quarry():
    return FeatureType.one(name=quarry)


@fixture(name='transport')
def get_transport(map, peasant, farm):
    u = map.add_unit(peasant, 0, 0)
    b = map.add_building(farm, 10, 10)
    t = u.set_transport(b)
    t.save()
    return t


@fixture(name='on_exploit')
def get_on_exploit():
    for name in (on_drop, on_exploit):
        register(name)
    yield
    for name in (on_drop, on_exploit):
        unregister(name)

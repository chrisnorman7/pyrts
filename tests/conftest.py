from pytest import fixture

from server.db import BuildingType, FeatureType, Map, MobileType, Player
from server.db.base import Base

Base.metadata.create_all()

password = 'TestsAreFun123'
farm = 'Farm'
peasant = 'Peasant'
field = 'Field'
stream = 'Stream'
mine = 'Mine'
forest = 'Forest'
quarry = 'Quarry'


@fixture(scope='session', autouse=True)
def create_stuff():
    Player.create('test', password, 'Test Player').save()
    BuildingType(name=farm, homely=True).save()
    MobileType(name=peasant).save()
    FeatureType(name=field, food=1).save()
    FeatureType(name=stream, water=1).save()
    FeatureType(name=mine, gold=1).save()
    FeatureType(name=forest, wood=1).save()
    FeatureType(name=quarry, stone=1).save()


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
    """Get the peasant mobile type."""
    return MobileType.one(name=peasant)


@fixture(name='mine')
def get_mine():
    return FeatureType.one(name=mine)


@fixture(name='quarry')
def get_quarry():
    return FeatureType.one(name=quarry)

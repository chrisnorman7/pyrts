from pytest import fixture

from server.db import (
    AttackType, Building, BuildingType, Feature, FeatureType, Map, Unit,
    UnitType, Player, setup, Transport
)
from server.events import (
    register, unregister, events, on_drop, on_exploit, on_heal, on_repair,
    on_attack
)
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
    ut.attack_type = AttackType.query().order_by(AttackType.strength).first()
    assert ut.attack_type is not None
    ut.stone = 1
    ut.heal_amount = 1
    ut.repair_amount = 1
    ut.auto_heal = True
    ut.auto_repair = True
    ut.save()
    assert options.start_building is not None


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
    p = Player.create('test', password, 'Test Player')
    p.save()
    return p


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
def set_on_exploit():
    for name in (on_drop, on_exploit):
        register(name)
    yield
    for name in (on_drop, on_exploit):
        unregister(name)


@fixture(autouse=True)
def delete_all():
    """Delete all database objects before a new test runs."""
    for cls in (Building, Feature, Player, Unit, Map, Transport):
        cls.query().delete()


@fixture(name='on_heal')
def set_on_heal():
    register(on_heal)
    yield
    unregister(on_heal)


@fixture(name='on_repair')
def set_on_repair():
    register(on_repair)
    yield
    unregister(on_repair)


@fixture(name='on_attack')
def set_on_attack():
    register(on_attack)
    yield
    unregister(on_attack)

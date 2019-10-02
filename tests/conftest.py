from pytest import fixture

from server.db import (
    AttackType, Building, BuildingType, FeatureType, Map, Unit, UnitType,
    Player, setup
)
from server.events import (
    register, unregister, events, on_attack, on_destroy, on_drop, on_exploit,
    on_heal, on_kill, on_repair
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
    for cls in (Building, Unit):
        cls.delete_all(cls.owner_id.isnot(None))
    Player.delete_all()
    p = Player.create('test', password, 'Test Player')
    p.save()
    return p


@fixture(name='farm')
def get_farm():
    """Get the farm building type."""
    bt = BuildingType.one(name=farm)
    Building.delete_all(type=bt)
    return bt


@fixture(name='peasant')
def get_peasant():
    """Get the peasant unit type."""
    ut = UnitType.one(name=peasant)
    Unit.delete_all(type=ut)
    return ut


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
    u.save()
    b = map.add_building(farm, 10, 10)
    b.save()
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
    event_names = (on_attack, on_kill, on_destroy)
    for event_name in event_names:
        register(event_name)
    yield
    for event_name in event_names:
        unregister(event_name)

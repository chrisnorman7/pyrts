from pytest import raises

from server.db import Player, Unit, UnitActions
from server.exc import NoActionRequired


def check_unit(
    unit, home, exploiting, material, target_coordinates, current_coordinates,
    action
):
    assert isinstance(unit, Unit)
    assert unit.home is home
    assert unit.exploiting is exploiting
    assert unit.exploiting_material == material
    assert unit.action is action
    assert unit.coordinates == current_coordinates
    assert unit.target == target_coordinates


def test_exploit(on_exploit, player, map, peasant, mine, farm):
    f = map.add_building(farm, 0, 0)
    p = map.add_unit(peasant, 0, 0)
    p.set_owner(player)
    p.home = f
    m = map.add_feature(mine, 2, 1)
    m.gold = 5
    for thing in (f, m, p):
        thing.save()
    args = (p, f, m, 'gold', m.coordinates)
    p.exploit(m, 'gold')
    check_unit(*args, (0, 0), UnitActions.exploit)
    Unit.progress(p.id)
    check_unit(*args, (1, 1), UnitActions.exploit)
    Unit.progress(p.id)
    check_unit(*args, m.coordinates, UnitActions.exploit)
    # It has reached the mine, let's make sure it exploits properly.
    Unit.progress(p.id)
    check_unit(*args, m.coordinates, UnitActions.drop)
    assert p.type.gold == 1
    assert p.gold == 1
    assert m.gold == 4
    Unit.progress(p.id)
    check_unit(*args, (1, 0), UnitActions.drop)
    Unit.progress(p.id)
    check_unit(*args, (0, 0), UnitActions.drop)
    assert f.gold == 0
    Unit.progress(p.id)
    check_unit(*args, f.coordinates, UnitActions.exploit)
    assert f.gold == 1
    Unit.progress(p.id)
    check_unit(*args, (1, 1), UnitActions.exploit)
    p.coordinates = m.coordinates
    m.gold = 0
    Unit.progress(p.id)
    check_unit(p, f, None, None, m.coordinates, m.coordinates, None)


def test_exploit_multiple(
    on_exploit, map, player, farm, mine, peasant, quarry
):
    b = map.add_building(farm, 0, 0)
    b.set_owner(player)
    m = map.add_feature(mine, 0, 0)
    m.gold = 100
    q = map.add_feature(quarry, 0, 0)
    q.stone = 100

    u = map.add_unit(peasant, 0, 0)
    u.set_owner(player)
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


def test_patrol(player, peasant, map, farm):
    p = map.add_unit(peasant, 0, 0)
    player.location = map
    f = map.add_building(farm, 0, 0)
    p.home = f
    p.set_owner(player)
    p.save()
    tc = (2, 2)
    args = (p, p.home, None, None)
    p.patrol(*tc)
    check_unit(*args, tc, (0, 0), UnitActions.patrol_out)
    Unit.progress(p.id)
    check_unit(*args, tc, (1, 1), UnitActions.patrol_out)
    Unit.progress(p.id)
    check_unit(*args, tc, tc, UnitActions.patrol_out)
    Unit.progress(p.id)
    check_unit(*args, tc, (2, 2), UnitActions.patrol_back)
    Unit.progress(p.id)
    check_unit(*args, tc, (1, 1), UnitActions.patrol_back)
    Unit.progress(p.id)
    check_unit(*args, tc, (0, 0), UnitActions.patrol_back)
    Unit.progress(p.id)
    check_unit(*args, tc, (0, 0), UnitActions.patrol_out)
    # Let's check they head out again.
    Unit.progress(p.id)
    check_unit(*args, tc, (1, 1), UnitActions.patrol_out)


def test_travel(player, peasant, map, farm):
    p = map.add_unit(peasant, 0, 0)
    player.location = map
    f = map.add_building(farm, 0, 0)
    p.home = f
    p.set_owner(player)
    p.save()
    tc = (2, 2)
    args = (p, p.home, None, None, tc)
    p.travel(*tc)
    check_unit(*args, (0, 0), UnitActions.travel)
    Unit.progress(p.id)
    check_unit(*args, (1, 1), UnitActions.travel)
    Unit.progress(p.id)
    check_unit(*args, tc, UnitActions.travel)
    Unit.progress(p.id)
    check_unit(*args, tc, None)


def test_heal(on_heal, player, peasant, map):
    p1 = map.add_unit(peasant, 0, 0)
    p2 = map.add_unit(peasant, 0, 0)
    player.location = map
    p1.set_owner(player)
    p2.set_owner(player)
    p2.health = 0
    player.save()  # Saves all related objects.
    args = (p1, p1.home, p2, None, p1.coordinates, p1.coordinates)
    p1.heal_unit(p2)
    check_unit(*args, UnitActions.heal)
    assert p2.health == 0
    Unit.progress(p1.id)
    check_unit(*args, UnitActions.heal)
    new_health = p2.health
    assert new_health > 0
    p2.health = p2.type.max_health - 1
    Unit.progress(p1.id)
    assert p2.health is None
    check_unit(p1, None, None, None, p1.coordinates, p1.coordinates, None)


def test_guard_heal(on_heal, peasant, map, player):
    player.location = map
    p1 = map.add_unit(peasant, 0, 0)
    p2 = map.add_unit(peasant, 0, 0)
    p2.health = 0
    for thing in (p1, p2):
        thing.set_owner(player)
    for thing in (p1, p2, player):
        thing.save()
    args = (
        p1, None, None, None, p1.coordinates, p1.coordinates, UnitActions.guard
    )
    p1.guard()
    check_unit(*args)
    Unit.progress(p1.id)
    check_unit(*args)
    assert p2.health > 0
    p2.health = peasant.max_health - 1
    Unit.progress(p1.id)
    check_unit(*args)
    assert p2.health is None


def test_guard_repair(on_repair, peasant, map, player, farm):
    player.location = map
    p = map.add_unit(peasant, 0, 0)
    f = map.add_building(farm, 0, 0)
    f.health = 0
    for thing in (p, f):
        thing.set_owner(player)
    for thing in (p, f, player):
        thing.save()
    args = (
        p, None, None, None, p.coordinates, p.coordinates, UnitActions.guard
    )
    p.guard()
    check_unit(*args)
    Unit.progress(p.id)
    check_unit(*args)
    assert f.health > 0
    f.health = farm.max_health - 1
    Unit.progress(p.id)
    check_unit(*args)
    assert f.health is None


def test_no_action(map, peasant):
    p = map.add_unit(peasant, 0, 0)
    with raises(NoActionRequired):
        p.guard_attack()
    with raises(NoActionRequired):
        p.guard_heal()
    with raises(NoActionRequired):
        p.guard_repair()


def test_attack(peasant, player, map, on_attack):
    opponent = Player.create('other_username', 'other_password', 'Other Player')
    p1 = map.add_unit(peasant, 0, 0)
    p2 = map.add_unit(peasant, 0, 0)
    player.location = map
    p1.set_owner(player)
    p2.set_owner(opponent)
    for obj in (p1, p2):
        obj.save()
    p1_args = (p1, None, p2, None, (0, 0), (0, 0), UnitActions.attack)
    p2_args = (p2, None, p1, None, (0, 0), (0, 0), UnitActions.attack)
    p1.attack(p2)
    check_unit(*p1_args)
    assert p2.action is None
    Unit.progress(p1.id)
    check_unit(*p1_args)
    check_unit(*p2_args)
    Unit.progress(p1.id)
    check_unit(*p1_args)
    assert p2.health < peasant.max_health
    Unit.progress(p2.id)
    check_unit(*p1_args)
    check_unit(*p2_args)
    assert p1.health < peasant.max_health
    p2.health = 0
    Unit.progress(p1.id)
    assert Unit.get(p2.id) is None
    check_unit(p1, None, None, None, p1.coordinates, p1.coordinates, None)

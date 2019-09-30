from server.db import Unit, UnitActions


def check_unit(
    unit, home, exploiting, material, target_coordinates, current_coordinates,
    action
):
    assert unit.home is home
    assert unit.exploiting is exploiting
    assert unit.target == target_coordinates
    assert unit.exploiting_material == material
    assert unit.coordinates == current_coordinates
    assert unit.action is action


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
    f = map.add_building(farm, 2, 2)
    p.home = f
    p.target = p.coordinates

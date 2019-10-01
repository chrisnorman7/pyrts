from time import time

from server.db import Building, Transport, Unit


def test_set_transport(map, transport):
    assert isinstance(transport, Transport)
    assert transport.id is not None
    assert transport.location is map
    u = transport.unit
    d = transport.destination
    assert isinstance(u, Unit)
    assert isinstance(d, Building)
    assert transport in d.incoming
    assert transport.land_time is None
    assert u.transport is transport


def test_launch(transport):
    u = transport.unit
    assert u.transport is transport
    started = time()
    transport.launch()
    u = transport.unit
    d = transport.destination
    assert u.location is None
    assert int(transport.land_time - started) == (u.type.speed * u.distance_to(
        d)
    )


def test_land(map, transport):
    u = transport.unit
    d = transport.destination
    u.location = None
    u.save()
    Transport.land(transport.id)
    assert u.location is transport.location
    assert u.coordinates == d.coordinates


def test_add_passenger(peasant, map, transport):
    u = map.add_unit(peasant, 0, 0)
    transport.add_passenger(u)
    assert u.location is None
    assert u.onboard is transport
    assert u in transport.passengers


def test_remove_passenger(peasant, map, transport):
    c = (0, 0)
    u = map.add_unit(peasant, *c)
    transport.add_passenger(u)
    transport.remove_passenger(u)
    assert u.location is map
    assert u.onboard is None
    assert u.coordinates == c


def test_delete_unit(peasant, map, transport):
    u = transport.unit
    assert u.transport is transport
    p1 = map.add_unit(peasant, 0, 0)
    p2 = map.add_unit(peasant, 0, 0)
    for obj in (p1, p2):
        transport.add_passenger(obj)
        obj.save()
    assert u.transport.passengers == [p1, p2]
    u.delete()
    assert Unit.get(u.id) is None
    assert Unit.get(p1.id) is None
    assert Unit.get(p2.id) is None
    assert Transport.get(transport.id) is None


def test_delete_building(peasant, map, transport):
    u = transport.unit
    b = transport.destination
    assert u.transport is transport
    p1 = map.add_unit(peasant, 0, 0)
    p2 = map.add_unit(peasant, 0, 0)
    for obj in (p1, p2):
        transport.add_passenger(obj)
        obj.save()
    assert transport.passengers == [p1, p2]
    b.delete()
    assert u.transport is None
    assert Building.get(b.id) is None
    assert Unit.get(p1.id) is p1
    assert Unit.get(p2.id) is p2
    assert Transport.get(transport.id) is None

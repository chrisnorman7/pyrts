"""Test the utility functions."""

from pytest import raises
from twisted.internet import reactor, base, defer
from db import Game, GameObject
from features import GameFeature, feature_types
from buildings import GameBuilding, building_types
from mobiles import GameMobile, mobile_types
from util import build


def test_build():
    """Build a building on an object."""
    building = GameBuilding('Test Building', pop_time=0)
    building_types[building.name] = building
    non_buildable = GameFeature('Non-Buildable Feature', buildable=False)
    feature_types[non_buildable.name] = non_buildable
    buildable = GameFeature('Buildable Feature', buildable=True)
    feature_types[buildable.name] = buildable
    mobile = GameMobile('TestMobile')
    mobile_types[mobile.name] = mobile
    game = Game()
    o = GameObject(game=game)
    o.type = mobile
    # The below should fail because you can't turn a mobile into a building.
    with raises(RuntimeError):
        build(o, building)
    o.type = non_buildable
    # The below should fail because you can't build on non-buildable land.
    with raises(RuntimeError):
        build(o, building)
    # The below should fail because you can't build anything except buildings.
    with raises(RuntimeError):
        build(o, mobile)
    o.type = buildable
    res = build(o, building)
    assert isinstance(res.delayed_call, base.DelayedCall)
    d = res.deferred
    assert isinstance(d, defer.Deferred)
    d.addCallback(lambda result: reactor.stop())
    # Now wait for it to do it:
    reactor.run()
    # Now test the result.
    assert o.type is building

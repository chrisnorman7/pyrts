"""Utility functions."""

from twisted.internet import reactor, defer
from attr import attrs, attrib
from objects import TYPE_FEATURE
from buildings import GameBuilding


@attrs
class BuildResult:
    """The result of a build call."""
    deferred = attrib()
    delayed_call = attrib()


def build(obj, thing):
    """Build thing on obj. This relies on obj.type_flag being TYPE_FEATURE, and
    obj.type.buildable being True."""
    if obj.type_flag != TYPE_FEATURE:
        raise RuntimeError('You can only build on empty land.')
    elif obj.type.buildable is not True:
        raise RuntimeError('You cannot build on a %s.' % obj.type.name)
    elif not isinstance(thing, GameBuilding):
        raise RuntimeError('You can only build buildings.')
    else:
        d = defer.Deferred()
        # Be prepared to accept the result (None) from twisted...
        d.addCallback(
            lambda result, obj=obj, thing=thing: setattr(
                obj,
                'type',
                thing
            ),
        )
        return BuildResult(
            d,
            reactor.callLater(
                thing.pop_time,
                d.callback,
                None
            )
        )


def object_created(obj):
    """Alert clients that an object has been created."""
    for player in obj.game.players:
        player.notify('{} created at ({}, {}).', obj.name, obj.x, obj.y)

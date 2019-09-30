"""Tests for the event framework."""

from pytest import raises
from server.events import (
    register, events, unregister, listen, unlisten, fire, EVENT_STOP,
    listen_multiple
)
from server.exc import DuplicateName, NoSuchEvent, NoSuchListener


class NoArgsWorks(Exception):
    pass


class WithArgsWorks(Exception):
    pass


def listen_no_args():
    raise NoArgsWorks


def listen_with_args(first, second, hello=None):
    assert first == 'test'
    assert second == 'this'
    assert hello == 'world'
    raise WithArgsWorks


def test_register():
    name = 'test_register'
    # Ensure name is returned.
    assert register(name) == name
    # Ensure name is added to the events dictionary with an empty list.
    assert events[name] == []
    # Ensure there is only one event.
    assert len(events) == 1
    # Make sure duplicates are noted.
    with raises(DuplicateName):
        register(name)


def test_unregister():
    name = 'test_unregister'
    # Ensure NoSuchEvent is raised if we try to unregister a hopefully
    # non-existant event.
    with raises(NoSuchEvent):
        unregister(name)
    # Register the event.
    register(name)
    # Then unregister it again.
    unregister(name)
    # Make sure it's gone.
    assert name not in events
    # And nothing else weird is going on.
    with raises(NoSuchEvent):
        unregister(name)


def test_listen():
    # First register an event.
    name = register('test_listen')
    listen(name)(print)
    assert len(events[name]) == 1
    assert events[name][0] is print
    listen(name)(map)
    assert len(events[name]) == 2
    assert events[name][1] is map
    # Ensure noting odd happened to the list.
    assert events[name][0] is print


def test_unlisten():
    name = 'test_unlisten'
    # Ensure that the code checks for the existance of a listener.
    with raises(NoSuchEvent):
        unlisten(name, print)
    # Register the event.
    register(name)
    # Listen for the event with a bogus function.
    listen(name)(print)
    unlisten(name, print)
    # Ensure there's no more entries.
    assert events[name] == []
    # Make sure NoSuchListener is raised when there's an event by the given
    # name, but without any listening functions.
    with raises(NoSuchListener):
        unlisten(name, print)
    # Let's make sure it gets the right function.
    for func in (print, map, filter):
        listen(name)(func)
    # Make sure all 3 are there.
    assert len(events[name]) == 3
    unlisten(name, map)
    # Make sure it removed the right one.
    assert events[name] == [print, filter]


def test_listen_multiple():
    names = ('listen_1', 'listen_2', 'listen_3')
    with raises(NoSuchEvent):
        listen_multiple(*names)(print)
    for name in names:
        register(name)
    listen_multiple(*names)(print)
    for name in names:
        assert name in events
        assert events[name] == [print]


def test_fire_basic():
    name = register('test_fire_basic')
    # Add a listener.
    listen(name)(lambda: None)
    # There's only one listener, so fire(name) should return 1.
    assert fire(name) == 1
    # Add another listener.
    listen(name)(lambda: EVENT_STOP)
    # Now it should be 2.
    assert fire(name) == 2
    # Add a third listener.
    listen(name)(lambda: None)
    # Because the second listener returns EVENT_STOP the result of fire(name)
    # should still be 2 because the third listener should never get called.
    assert fire(name) == 2


def test_fire_advanced():
    name = register('test_fire_no_args')
    listen(name)(listen_no_args)
    with raises(NoArgsWorks):
        fire(name)
    name = register('test_fire_with_args')
    listen(name)(listen_with_args)
    with raises(WithArgsWorks):
        fire(name, 'test', 'this', hello='world')

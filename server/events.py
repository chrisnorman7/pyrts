"""Provides the register, and listen methods, as well as the constants
event_continue, and event_stop."""

from .exc import DuplicateName, NoSuchEvent, NoSuchListener

events = {}

EVENT_CONTINUE = None
EVENT_STOP = True


def register(name):
    """Register an event with the given name. If name already exists,
    DuplicateName is raised."""
    if name in events:
        raise DuplicateName(name)
    events[name] = []
    return name


def unregister(name):
    """Unregisters the event with the given name. If the event does not exist,
    NoSuchEvent will be raised."""
    if name not in events:
        raise NoSuchEvent(name)
    del events[name]


def listen(thing):
    """A decorator to make an event listener. If thing is callable then it is
    assumed to be a function with an __name__ attribute which will be used as
    the name of the event to listen for. If not then it is assumed to be the
    name of the event to listen for, and a decorator function is returned.

    As such, this method has two forms:

    @listen('event_name')
    def func(...):
        pass

    @listen
    def event_name(...):
        pass
    """

    def outer(name):
        """Takes a name and returns inner."""
        def inner(func):
            if name is None:
                _name = func.__name__
            else:
                _name = name
            if _name not in events:
                raise NoSuchEvent(_name)
            events[_name].append(func)
            return func
        return inner

    if callable(thing):
        return outer(None)(thing)
    return outer(thing)


def unlisten(name, func):
    """Stop func listening for the event with the given name. If there is no
    event by that name, NoSuchEvent is raised. If func is not listening for the
    event, NoListenerException will be raised."""
    if name not in events:
        raise NoSuchEvent(name)
    if func not in events[name]:
        raise NoSuchListener(func)
    events[name].remove(func)


def listen_multiple(*names):
    """A decorator that allows you to listen to multiple events with one
    function."""

    def inner(func):
        for name in names:
            listen(name)(func)
        return func

    return inner


def fire(name, *args, **kwargs):
    """Fire the named event, passing args and kwargs to every function that is
    listening. If there is no event by that name, NoSuchEvent is raised. If any
    of the functions returns EVENT_STOP then execution will stop. This function
    returns the number of functions which have been called."""
    if name not in events:
        raise NoSuchEvent(name)
    n = 0
    for func in events[name]:
        n += 1
        if func(*args, **kwargs) is EVENT_STOP:
            break
    return n


on_attack = register('on_attack')
on_exploit = register('on_exploit')
on_drop = register('on_drop')
on_heal = register('on_heal')
on_repair = register('on_repair')
on_exhaust = register('on_exhaust')

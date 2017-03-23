"""Provides the BaseObject class."""

from attr import attrs, attrib, Factory

# Type flags:
TYPE_FEATURE = 0
TYPE_MOBILE = 1
TYPE_BUILDING = 2


def build_flags(dict, *keys):
    """Given 1 or more keys, return dict[key1] | dict[key2] | ...."""
    res = 0
    for key in keys:
        res |= dict[key]
    return res


def build_names(dict, flags):
    """Given flags as an integer, return a list of all the keys from dict which
    are present."""
    res = []
    for key, value in dict.items():
        if flags & value:
            res.append(key)
    return res


@attrs
class BaseObject:
    """The very basic object of the game."""
    name = attrib()
    # Food, wood, gold, and water.
    #
    # For mobiles and buildings these are the resources which must be gathered
    # before this object can be created.
    # For Feature objects, it is the resources they contain.
    food = attrib(default=Factory(lambda: 2))
    wood = attrib(default=Factory(lambda: 2))
    gold = attrib(default=Factory(lambda: 4))
    water = attrib(default=Factory(lambda: 2))

    def __str__(self):
        return self.name


@attrs
class ObjectWithHP(BaseObject):
    """The base for both mobs and buildings."""
    max_hp = attrib(default=Factory(lambda: 40))
    pop_time = attrib(default=Factory(lambda: 60))
    # Max HP regained per tick:
    constitution = attrib(default=Factory(lambda: 1))

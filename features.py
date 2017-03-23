"""Land features like forests, lakes (and rivers) and gold mines."""

from random import randint
from attr import attrs, attrib, Factory
from objects import BaseObject, build_flags, TYPE_FEATURE

# Affects:
affects = {
    'rain': 1,
    'sun': 2,
}


@attrs
class GameFeature(BaseObject):
    """A land-based feature."""
    # If random is set to True, wood, water, gold, and food will all be
    # randomised.
    random = attrib(default=Factory(lambda: True))
    affects = attrib(default=Factory(lambda: 0))
    buildable = attrib(default=Factory(lambda: False))

    def __attrs_post_init__(self):
        self.type_flag = TYPE_FEATURE
        if self.random:
            for attr in ['wood', 'food', 'water', 'gold']:
                setattr(self, attr, randint(0, getattr(self, attr)))


_features = [
    GameFeature(
        'Gold Mine',
        wood=0,
        water=0,
        gold=10000,
        food=0,
    ),
    GameFeature(
        'Lake',
        wood=0,
        gold=0,
        food=400,
        water=10000,
        affects=build_flags(affects, 'rain')
    ),
    GameFeature(
        'Forest',
        wood=10000,
        food=200,
        water=100,
        gold=0,
        affects=build_flags(affects, 'sun', 'rain')
    ),
    GameFeature(
        'Empty Land',
        random=False,
        wood=0,
        food=0,
        water=0,
        gold=0,
        buildable=True
    )
]

feature_types = {x.name: x for x in _features}

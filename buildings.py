"""Game buildings."""

from attr import attrs, attrib, Factory
from objects import ObjectWithHP, TYPE_BUILDING
from mobiles import mobile_types


@attrs
class GameBuilding(ObjectWithHP):
    """A building in the game."""
    # Mobiles this building produces:
    provides = attrib(default=Factory(list))
    # Things which have to be built before this building can be constructed:
    depends = attrib(default=Factory(list))

    def __attrs_post_init__(self):
        self.type_flag = TYPE_BUILDING


town_hall = GameBuilding(
    'Town Hall',
    pop_time=2*60,
    provides=[mobile_types['Labourer']],
    max_hp=100
)

_buildings = [
    town_hall
]

building_types = {x.name: x for x in _buildings}

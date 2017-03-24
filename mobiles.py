"""Game types."""

from attr import attrs, attrib, Factory
from objects import ObjectWithHP, build_flags, TYPE_MOBILE


# Attack types:
attack_types = {
    'ground': 1,
    'air': 2,
    'water': 4
}

# Weapon types:
weapon_types = {
    'fist': 1,
    'sword': 2,
    'bow and arrow': 4,
    'fire': 8,
    'magic': 16,
    'artilary': 32
}

# Skills:
skills = {
    'build': 1,  # Includes repair.
    'mine': 2,
    'log': 4,
    'harvest': 8,
    'collect water': 16
}


@attrs
class GameMobile(ObjectWithHP):
    """Game mobile."""
    max_mana = attrib(default=Factory(lambda: 0))
    skills = attrib(default=Factory(lambda: 0))
    attack_type = attrib(default=Factory(lambda: 0))
    weapon_type = attrib(default=Factory(lambda: 0))
    speed = attrib(default=Factory(lambda: 1))

    def __attrs_post_init__(self):
        self.type_flag = TYPE_MOBILE


_mobiles = [
    GameMobile(
        'Labourer',
        skills=build_flags(skills, 'build', 'mine', 'log', 'harvest'),
        speed=10,
        pop_time=25
    ),
    GameMobile(
        'Water Collecter',
        skills=build_flags(skills, 'collect water'),
        speed=15,
        pop_time=10
    ),
    GameMobile(
        'Brawler',
        attack_type=build_flags(attack_types, 'ground'),
        weapon_type=build_flags(weapon_types, 'fist'),
        skills=build_flags(skills, 'mine', 'log', 'harvest'),
        speed=4,
    ),
    GameMobile(
        'Foot Soldier',
        attack_type=build_flags(attack_types, 'ground'),
        weapon_type=build_flags(weapon_types, 'fist', 'sword'),
        speed=3,
        pop_time=20
    ),
    GameMobile(
        'Horseman',
        attack_type=build_flags(attack_types, 'ground'),
        weapon_type=build_flags(weapon_types, 'fist', 'sword'),
        pop_time=40
    )
]


mobile_types = {x.name: x for x in _mobiles}

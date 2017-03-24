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
    'gold': 2,
    'wood': 4,
    'food': 8,
    'water': 16
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
        skills=build_flags(skills, 'build', 'gold', 'wood', 'food'),
        speed=10,
        pop_time=10
    ),
    GameMobile(
        'Water Collecter',
        skills=build_flags(skills, 'water'),
        speed=15,
        pop_time=10,
        gold=1,
        wood=0,
        food=1,
        water=0
    ),
    GameMobile(
        'Brawler',
        attack_type=build_flags(attack_types, 'ground'),
        weapon_type=build_flags(weapon_types, 'fist'),
        skills=build_flags(skills, 'gold', 'wood', 'food'),
        speed=4,
        wood=0,
        gold=10,
        food=8,
        water=3
    ),
    GameMobile(
        'Foot Soldier',
        attack_type=build_flags(attack_types, 'ground'),
        weapon_type=build_flags(weapon_types, 'fist', 'sword'),
        speed=3,
        pop_time=20,
        gold=15,
        wood=0,
        food=10,
        water=15
    ),
    GameMobile(
        'Horseman',
        attack_type=build_flags(attack_types, 'ground'),
        weapon_type=build_flags(weapon_types, 'fist', 'sword'),
        pop_time=40,
        wood=5,
        gold=20,
        food=15,
        water=15
    )
]


mobile_types = {x.name: x for x in _mobiles}

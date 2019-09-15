"""This script will bootstrap the database to a minimal level for usage.

You will be left with the following buildings:
* Town Hall (homely).
* Farm (requires Town Hall).
* University (requires Farm)

You will be left with the following mobiles:
* Peasant (provided by Town Hall).
Peasants can build town halls and farms, and can exploit wood, and gold.
* Farmer (provided by Farm)
Farmers can build farms and universities, and can exploit food, water, and
wood.
* Stonemason (provided by university)
* Stonemasons can't build anything, but can exploit stone.
* Engineer (provided by university)
Engineers can automatically repair any damaged building at the coordinates they
are guarding.

You will be left with the following land features:
* Mine (provides gold)
* Quarry (provides stone)
* Lake (provides water)
* Forest (provides wood)
* Field (provides food)
"""

import os.path

from server.db import BuildingType, FeatureType, MobileType, dump
from server.db.util import _filename as fn


def main():
    if os.path.isfile(fn):
        return print('Refusing to continue with existing database file.')
    town_hall = BuildingType(
        name='Town Hall', homely=True, gold=15, wood=30, stone=10
    )
    farm = BuildingType(
        name='Farm', depends=town_hall, gold=5, wood=5, stone=1, max_health=22
    )
    university = BuildingType(
        name='University', depends=farm, wood=30, stone=15, gold=30,
        max_health=30
    )
    for thing in (town_hall, farm, university):
        thing.save()
    peasant = MobileType(
        name='Peasant', wood=1, gold=1, max_health=15, speed=12
    )
    farmer = MobileType(name='Farmer', food=1, water=1, speed=10)
    stonemason = MobileType(
        name='Stonemason', stone=1, max_health=25, speed=18
    )
    engineer = MobileType(name='Engineer', auto_repair=True)
    for thing in (peasant, farmer, stonemason, engineer):
        thing.save()
    for b in (town_hall, farm):
        peasant.add_building(b).save()
    town_hall.add_recruit(peasant, food=1, water=1, gold=3).save()
    for b in (farm, university):
        farmer.add_building(b).save()
    farm.add_recruit(farmer, food=2, gold=4, water=2).save()
    university.add_recruit(stonemason, food=4, water=5, gold=6).save()
    university.add_recruit(engineer, food=3, water=4, gold=15).save()
    FeatureType(name='Mine', gold=1).save()
    FeatureType(name='Quarry', stone=1).save()
    FeatureType(name='Lake', water=1).save()
    FeatureType(name='Forest', wood=1).save()
    FeatureType(name='Field', food=1).save()
    dump()
    print('Done.')


if __name__ == '__main__':
    main()

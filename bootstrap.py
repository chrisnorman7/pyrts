"""This script will bootstrap the database to a minimal level for usage.

You will be left with the following buildings:
* Town Hall (homely).
* Farm (requires Town Hall).
* Stable (requires Farm)

You will be left with the following land features:
* Mine (provides gold)
* Quarry (provides stone)
* Lake (provides water)
* Forest (provides wood)
* Field (provides food)

You will be left with the following mobiles:
* Peasant (provided by Town Hall).
Peasants can build town halls and farms, and can exploit wood, and gold.
* Farmer (provided by Farm)
Farmers can build farms and stables, and can exploit food, water, and wood.
* Scout (provided by Stable)
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
        name='Farm', depends=town_hall, gold=5, wood=5, stone=1
    )
    stable = BuildingType(
        name='Stable', depends=farm, wood=30, stone=15, gold=30
    )
    for thing in (town_hall, farm, stable):
        thing.save()
    peasant = MobileType(name='Peasant', wood=1, gold=1)
    farmer = MobileType(name='Farmer', food=1, water=1)
    scout = MobileType(name='Scout', stone=1)
    for thing in (peasant, farmer, scout):
        thing.save()
    peasant.add_building(town_hall)
    peasant.add_building(farm)
    town_hall.add_recruit(peasant, food=1, water=1, gold=3).save()
    farmer.add_building(farm)
    farm.add_recruit(farmer, food=2, gold=4, water=2)
    stable.add_recruit(scout, food=4, water=5, gold=6)
    FeatureType(name='Mine', gold=1).save()
    FeatureType(name='Quarry', stone=1).save()
    FeatureType(name='Lake', water=1).save()
    FeatureType(name='Forest', wood=1).save()
    FeatureType(name='Field', food=1).save()
    dump()
    print('Done.')


if __name__ == '__main__':
    main()

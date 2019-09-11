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
* Farmer (provided by Farm)
* Scout (provided by Stable)
"""

import os.path

from server.db import BuildingType, FeatureType, MobileType, dump
from server.db.util import _filename as fn


def main():
    if os.path.isfile(fn):
        return print('Refusing to continue with existing database file.')
    town_hall = BuildingType(name='Town Hall', homely=True)
    town_hall.save()
    farm = BuildingType(name='Farm', depends=town_hall)
    farm.save()
    stable = BuildingType(name='Stable', depends=farm)
    stable.save()
    peasant = MobileType(name='Peasant')
    peasant.save()
    town_hall.recruits.append(peasant)
    farmer = MobileType(name='Farmer')
    farmer.save()
    farm.recruits.append(farmer)
    scout = MobileType(name='Scout')
    scout.save()
    stable.recruits.append(scout)
    FeatureType(name='Mine', gold=1).save()
    FeatureType(name='Quarry', stone=1).save()
    FeatureType(name='Lake', water=1).save()
    FeatureType(name='Forest', wood=1).save()
    FeatureType(name='Field', food=1).save()
    dump()
    print('Done.')


if __name__ == '__main__':
    main()

"""Check for inconsistancies in the database."""

from server.db import (
    BuildingBuilder, BuildingRecruit, BuildingType, load, UnitType
)


def main():
    load()
    for name in UnitType.resource_names():
        if UnitType.count(getattr(UnitType, name) >= 1):
            continue
        else:
            print(f'There is no unit that can gather {name}.')
    for bt in BuildingType.all():
        if not BuildingBuilder.count(building_type_id=bt.id):
            print(f'There is no way to build {bt.name}.')
    for ut in UnitType.all():
        if not BuildingRecruit.count(unit_type_id=ut.id):
            print(f'There is no way to recruit {ut.get_name()}.')


if __name__ == '__main__':
    try:
        main()
    except FileNotFoundError:
        print('No database file exists.')

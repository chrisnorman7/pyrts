import os
import os.path

from shutil import rmtree

from yaml import dump

from server.db import (
    load, UnitType, FeatureType, BuildingType, dump_object, AttackType, setup
)
from server.options import options

load()
setup()

if os.path.isdir('types'):
    rmtree('types')
    print('Deleted types directory.')
for cls in (UnitType, BuildingType, FeatureType, AttackType):
    path = os.path.join('types', cls.__name__)
    if not os.path.isdir(path):
        os.makedirs(path)
        print(f'Created directory {path}.')
    for obj in cls.all():
        d = dump_object(obj)
        if obj is options.start_building:
            d['start_building'] = True
        del d['id']
        if isinstance(obj, BuildingType) and obj.depends is not None:
            del d['depends_id']
            d['depends'] = obj.depends.name
        if isinstance(obj, UnitType):
            if obj.attack_type is not None:
                d['attack'] = obj.attack_type.name
                del d['attack_type_id']
            d['buildings'] = [b.name for b in obj.can_build]
            d['recruits'] = []
            for bt in obj.recruiters:
                bm = bt.get_recruit(obj)
                rd = dump_object(bm)
                for name in ('id', 'unit_type_id', 'building_type_id'):
                    del rd[name]
                rd['building'] = bt.name
            d['recruits'].append(rd)
        filename = os.path.join(path, f'{obj.name}.yaml')
        print(f'Dumped {obj.name} to {filename}.')
        with open(filename, 'w') as f:
            dump(d, stream=f)

import os
import os.path

from yaml import dump

from server.db import load, MobileType, FeatureType, BuildingType, dump_object

load()

for cls in (MobileType, BuildingType, FeatureType):
    path = os.path.join('types', cls.__name__)
    if not os.path.isdir(path):
        os.makedirs(path)
        print(f'Created directory {path}.')
    for obj in cls.all():
        d = dump_object(obj)
        del d['id']
        if isinstance(obj, BuildingType) and obj.depends is not None:
            del d['depends_id']
            d['depends'] = obj.depends.name
        if isinstance(obj, MobileType):
            d['buildings'] = [b.name for b in obj.can_build]
            d['recruits'] = []
            for bt in obj.recruiters:
                bm = bt.get_recruit(obj)
                rd = dump_object(bm)
                for name in ('id', 'mobile_type_id', 'building_type_id'):
                    del rd[name]
                rd['building'] = bt.name
            d['recruits'].append(rd)
        filename = os.path.join(path, f'{obj.name}.yaml')
        print(f'Dumped {obj.name} to {filename}.')
        with open(filename, 'w') as f:
            dump(d, stream=f)

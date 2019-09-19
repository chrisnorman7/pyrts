"""Provides utility functions."""

import logging
import os
import os.path
from glob import glob

from db_dumper import dump as db_dump, load as db_load
from sqlalchemy import inspect
from sqlalchemy.exc import InvalidRequestError
from yaml import dump as yaml_dump, load as yaml_load, FullLoader

from .base import Base
from .buildings import BuildingType
from .features import FeatureType
from .mobiles import MobileType
from .session import session

from ..exc import InvalidName

logger = logging.getLogger(__name__)
_filename = 'db.yaml'


def all_objects():
    """Get a list of all objects."""
    items = []
    for cls in Base.classes():
        items.extend(cls.all())
    return items


def dump_object(obj):
    """Dump a single object."""
    cls = type(obj)
    columns = inspect(cls).c
    data = {}
    for column in columns:
        name = column.name
        value = getattr(obj, name)
        default = column.default
        if default is not None:
            default = default.arg
        if value != default:
            data[name] = value
    return data


def dump_objects():
    return db_dump(all_objects(), dump_object)


def load_objects(d):
    """Load all objects from a dictionary d."""
    session.add_all(db_load(d, Base.classes()))


def dump(filename=None):
    """Dump all objects to the given filename, which defaults to db.yaml."""
    if filename is None:
        filename = _filename
    d = dump_objects()
    with open(filename, 'w') as f:
        yaml_dump(d, stream=f)


def load(filename=None):
    """Load from the given filename, which defaults to db.yaml."""
    if filename is None:
        filename = _filename
    with open(filename, 'r') as f:
        data = yaml_load(f, Loader=FullLoader)
    load_objects(data)


def get_object_by_name(cls, name):
    """Get an object of type cls by the given name. If no name is found,
    InvalidName(cls, name) will be raised."""
    try:
        return cls.one(name=name)
    except InvalidRequestError:
        raise InvalidName(cls, name)


def bootstrap():
    """Load all types in the types directory."""
    depends = {}
    buildings = {}
    recruits = {}
    for cls in (FeatureType, BuildingType, MobileType):
        logger.info('Checking class %s.', cls)
        path = os.path.join('types', cls.__name__, '*.yaml')
        for filename in glob(path):
            with open(filename, 'r') as f:
                d = yaml_load(f, FullLoader)
            if cls is MobileType:
                _buildings = d.pop('buildings', [])
                _recruits = d.pop('recruits', [])
            elif cls is BuildingType:
                _depends = d.pop('depends', None)
            if 'id' in d:
                del d['id']
            if not cls.count(**d):
                obj = cls(**d)
                obj.save()
                logger.info('Created %s (#%d).', obj, obj.id)
            else:
                logger.info('Skipping %s.', d['name'])
                continue
            if cls is MobileType:
                buildings[obj.id] = _buildings
                recruits[obj.id] = _recruits
            elif cls is BuildingType:
                depends[obj.id] = _depends
    for mt in MobileType.all():
        for name in buildings.get(mt.id, []):
            bt = get_object_by_name(BuildingType, name)
            mt.can_build.append(bt)
            logger.info('%s can build %s.', mt, bt)
        for r in recruits.get(mt.id, []):
            building_type_name = r.pop('building')
            bt = get_object_by_name(BuildingType, building_type_name)
            bt.add_recruit(mt, **r).save()
            logger.info('%s can recruit %s.', bt, mt)
        mt.save()
    for bt in BuildingType.all():
        name = depends.get(bt.id, None)
        if name is not None:
            bt.depends = get_object_by_name(BuildingType, name)
            bt.save()

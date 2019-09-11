"""Provides utility functions."""

from db_dumper import dump as db_dump, load as db_load
from sqlalchemy import inspect
from yaml import dump as yaml_dump, load as yaml_load, FullLoader

from .base import Base
from .session import session

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

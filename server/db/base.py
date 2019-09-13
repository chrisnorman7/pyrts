"""Provides the Base class, as well as several useful mixins."""

import os.path

from inspect import isclass
from urllib.parse import quote

from sqlalchemy import Column, Integer, String, ForeignKey, inspect
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from .engine import engine
from .session import session

from ..exc import NoSuchSound
from ..options import sounds_path, base_url
from ..util import english_list


class _Base:
    id = Column(Integer, primary_key=True)

    def save(self):
        """Save this object."""
        session.add(self)
        try:
            session.commit()
        except DatabaseError:
            session.rollback()
            raise

    def delete(self):
        session.delete(self)
        try:
            session.commit()
        except DatabaseError:
            session.rollback()
            raise

    @classmethod
    def query(cls, *args, **kwargs):
        """Return a query object with this class."""
        return session.query(cls).filter(*args).filter_by(**kwargs)

    @classmethod
    def count(cls, *args, **kwargs):
        """Return the number of instances of this class in the database."""
        return cls.query(*args, **kwargs).count()

    @classmethod
    def first(cls, *args, **kwargs):
        """Return the first instance of this class in the database."""
        return cls.query(*args, **kwargs).first()

    @classmethod
    def get(cls, id):
        """Get an object with the given id."""
        return cls.query().get(id)

    @classmethod
    def one(cls, *args, **kwargs):
        return cls.query(*args, **kwargs).one()

    @classmethod
    def all(cls, *args, **kwargs):
        """Return all child objects."""
        return cls.query(*args, **kwargs).all()

    @classmethod
    def classes(cls):
        """Return all table classes."""
        for item in cls._decl_class_registry.values():
            if isclass(item) and issubclass(item, cls):
                yield item

    @classmethod
    def number_of_objects(cls):
        """Returns the number of objects in the database."""
        count = 0
        for base in cls.classes():
            count += base.count()
        return count

    def __repr__(self):
        name = type(self).__name__
        string = '%s (' % name
        attributes = []
        i = inspect(type(self))
        for column in i.c:
            name = column.name
            attributes.append('%s=%r' % (name, getattr(self, name)))
        string += ', '.join(attributes)
        return string + ')'


Base = declarative_base(bind=engine, cls=_Base)


class CoordinatesMixin:
    x = Column(Integer, nullable=False, default=0)
    y = Column(Integer, nullable=False, default=0)

    @property
    def coordinates(self):
        return self.x, self.y

    @coordinates.setter
    def coordinates(self, value):
        self.x, self.y = value


class NameMixin:
    name = Column(String(30), nullable=False)

    @classmethod
    def alphabetized(cls, *args, **kwargs):
        """Return a list of items, sorted by name."""
        return cls.query(*args, **kwargs).order_by(cls.name)

    def __str__(self):
        return self.name


class LocationMixin:
    @declared_attr
    def location_id(cls):
        return Column(Integer, ForeignKey('maps.id'), nullable=True)

    @declared_attr
    def location(cls):
        return relationship(
            'Map', backref=cls.__tablename__, foreign_keys=[cls.location_id],
            remote_side='Map.id'
        )


class OwnerMixin:
    @declared_attr
    def owner_id(cls):
        return Column(Integer, ForeignKey('players.id'), nullable=True)

    @declared_attr
    def owner(cls):
        return relationship(
            'Player', backref=f'owned_{cls.__tablename__}',
            foreign_keys=[cls.owner_id], remote_side='Player.id'
        )


class ResistanceMixin:
    resistance = Column(Integer, nullable=False, default=1)


class TypeMixin:
    @declared_attr
    def type_id(cls):
        type_class = cls.__type_class__
        return Column(
            Integer, ForeignKey(type_class.__tablename__ + '.id'),
            nullable=False
        )

    @declared_attr
    def type(cls):
        type_class = cls.__type_class__
        return relationship(type_class.__name__, backref=cls.__tablename__)


class ResourcesMixin:
    food = Column(Integer, nullable=True)
    water = Column(Integer, nullable=True)
    gold = Column(Integer, nullable=True)
    wood = Column(Integer, nullable=True)
    stone = Column(Integer, nullable=True)

    @classmethod
    def resource_names(cls):
        return [
            x for x in dir(ResourcesMixin) if
            not x.startswith('_') and x not in [
                'resources_string', 'resource_names'
            ]
        ]

    def resources_string(self):
        res = []
        for name in type(self).resource_names():
            value = getattr(self, name)
            if value not in (None, 0):
                res.append(f'{value} {name}')
        return english_list(res, empty='Free')


class SoundMixin:

    @property
    def sound(self):
        path = os.path.join(sounds_path, 'amb', self.__tablename__, self.name)
        path += '.wav'
        if os.path.isfile(path):
            url = quote(path.replace(os.path.sep, '/'))
            return f'{base_url}{url}?{os.path.getmtime(path)}'
        raise NoSuchSound(path)


class GetNameMixin:
    def get_name(self):
        if self.owner is None:
            append = ''
        else:
            results = getattr(self.owner, f'owned_{self.__tablename__}')
            index = results.index(self) + 1
            append = f' {index}'
        return self.type.name + append


class MaxHealthMixin:
    max_health = Column(Integer, nullable=False, default=20)


class HealthMixin:
    health = Column(Integer, nullable=True)

    @property
    def max_hp(self):
        return self.type.max_health

    @property
    def hp(self):
        if self.health is None:
            return self.type.max_health
        return self.health

    @hp.setter
    def hp(self, value):
        if value == self.max_hp:
            value = None
        self.health = value

    def heal(self, amount):
        """Heal this object to a maximum of self.max_health."""
        self.hp = min(self.max_hp, self.hp + amount)

"""Provides the Base class, as well as several useful mixins."""

import os.path

from datetime import datetime
from inspect import isclass
from urllib.parse import quote

from sqlalchemy import Column, Integer, String, ForeignKey, inspect, DateTime
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from .engine import engine
from .session import session

from ..exc import NoSuchSound
from ..options import options
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

    @classmethod
    def get_class_from_table(cls, table):
        """Return the class whose __table__ attribute is the provided Table
        instance."""
        for value in cls._decl_class_registry.values():
            if getattr(value, '__table__', None) is table:
                return value


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

    def distance_to(self, other):
        """Return the distance between this object and other."""
        dx = max(self.x, other.x) - min(self.x, other.x)
        dy = max(self.y, other.y) - min(self.y, other.y)
        return max(dx, dy)

    def directions_to(self, other):
        """Return textual directions to an object other."""
        if other.x == self.x:
            direction_x = None
        elif other.x > self.x:
            direction_x = 'east'
        else:
            direction_x = 'west'
        if other.y == self.y:
            direction_y = None
        elif other.y > self.y:
            direction_y = 'north'
        else:
            direction_y = 'south'
        if direction_y is not None:
            dy = max(self.y, other.y) - min(self.y, other.y)
            string = f'{dy} {direction_y}'
        else:
            string = ''
        if direction_x is not None:
            dx = max(self.x, other.x) - min(self.x, other.x)
            if string:
                string += ', '
            string += f'{dx} {direction_x}'
        if string:
            return string
        return 'here'


class NameMixin:
    name = Column(String(30), nullable=False)

    @classmethod
    def alphabetized(cls, *args, **kwargs):
        """Return a list of items, sorted by name."""
        return cls.query(*args, **kwargs).order_by(cls.name)

    def get_name(self):
        """Use GetNameMixin to get a name."""
        return GetNameMixin.get_name(self)

    def __str__(self):
        return self.get_name()


class GetNameMixin:
    def get_name(self):
        """Return this object's name."""
        cls = type(self)
        if TypeMixin not in cls.__bases__:
            return self.name
        if OwnerMixin in cls.__bases__:
            kwargs = dict(owner=self.owner)
        else:
            kwargs = {}
        results = cls.all(type=self.type, **kwargs)
        index = results.index(self) + 1
        return f'{self.type.name} {index}'


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
    updated = Column(
        DateTime(timezone=True), nullable=True, onupdate=datetime.utcnow,
        default=datetime.utcnow
    )

    @declared_attr
    def owner_id(cls):
        return Column(Integer, ForeignKey('players.id'), nullable=True)

    @declared_attr
    def owner(cls):
        return relationship(
            'Player', backref=backref(
                f'owned_{cls.__tablename__}', order_by=cls.updated
            ), foreign_keys=[cls.owner_id], remote_side='Player.id'
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
                'resources', 'resources_dict', 'resources_string',
                'resource_names', 'get_difference', 'take_requirements'
            ]
        ]

    @property
    def resources(self):
        """Return a list of names representing the resources this feature type
        provides."""
        names = []
        for name in type(self).resource_names():
            if getattr(self, name) is not None:
                names.append(name)
        return names

    def resources_dict(self):
        """Return a dictionary of name: value pairs, where name is the name of
        a resource, and value is the value of that resource on this object."""
        return {name: getattr(self, name) for name in self.resources}

    def resources_string(self, empty='free'):
        """Return a string explaining this object's resources. This string can
        be sent directly to a player."""
        d = self.resources_dict()
        resource_names = sorted(d, key=lambda name: d[name])
        resources = {name: d[name] for name in resource_names}
        res = []
        for name, value in resources.items():
            res.append(f'{value} {name}')
        return english_list(res, empty=empty)

    def get_difference(self, thing):
        """Return a dictionary containing name: value pairs for every resource
        on thing that is less than the same resource on this object."""
        d = {}
        for name in self.resources:
            required = getattr(self, name)
            value = getattr(thing, name)
            if value is None:
                continue
            if value < required:
                d[name] = required - value
        return d

    def take_requirements(self, thing):
        """Take the resources required by thing from this object."""
        for name in thing.resources:
            required = getattr(thing, name)
            value = getattr(self, name)
            setattr(self, name, value - required)


class SoundMixin:

    @property
    def sound(self):
        path = os.path.join(
            options.sounds_path, 'amb', self.__tablename__, self.name
        )
        path += '.wav'
        if os.path.isfile(path):
            url = quote(path.replace(os.path.sep, '/'))
            return f'{options.base_url}{url}?{os.path.getmtime(path)}'
        raise NoSuchSound(path)


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


class StrengthMixin:
    strength = Column(Integer, nullable=False, default=1)

"""Provides the Map class."""

from datetime import datetime
from random import randint

from sqlalchemy import Column, Boolean, DateTime, Integer

from .base import Base, NameMixin, OwnerMixin
from .buildings import Building
from .entry_points import EntryPoint
from .features import Feature
from .units import Unit
from .util import dump_object

from ..options import options
from ..util import pluralise


class Map(Base, NameMixin, OwnerMixin):
    """A map for game play."""

    __tablename__ = 'maps'
    size_x = Column(Integer, nullable=False, default=25)
    size_y = Column(Integer, nullable=False, default=25)
    template = Column(Boolean, nullable=False, default=True)
    finalised = Column(DateTime(timezone=True), nullable=True)

    def finalise(self):
        """Mark this map as finalised."""
        self.finalised = datetime.utcnow()
        self.broadcast(
            'All players are present. The game begins.', sound='start.wav'
        )

    def add_entry_point(self, x, y):
        """Add an entry point to this map at the given coordinates."""
        return EntryPoint(location=self, x=x, y=y)

    def add_building(self, type, x, y):
        """Add a building to this map."""
        return Building(
            location=self, type=type, x=x, y=y,
            **{name: 0 for name in Building.resource_names()}
        )

    def add_feature(self, type, x, y):
        """Add a feature to this map."""
        f = Feature(location=self, type=type, x=x, y=y)
        for name in type.resources:
            setattr(f, name, 0)
        return f

    def add_unit(self, type, x, y):
        """Add a unit to this map."""
        m = Unit(location=self, type=type, x=x, y=y)
        for name in Unit.resource_names():
            setattr(m, name, 0)
        return m

    def broadcast(self, text, sound=None):
        """Broadcast a message to all players on this map."""
        for player in self.players:
            player.message(text)
            if sound is not None:
                player.sound(sound)

    def copy(self):
        """Return a duplicated version of this map."""
        cls = type(self)
        data = dump_object(self)
        del data['id']
        data['template'] = False
        m = cls(**data)
        objects = {}
        for name, cls in (
            ('buildings', Building),
            ('features', Feature),
            ('units', Unit),
            ('entry_points', EntryPoint)
        ):
            objects[cls] = {}
            for thing in getattr(self, name):
                data = dump_object(thing)
                del data['id']
                del data['location_id']
                if cls is Unit:
                    del data['home_id']
                o = cls(**data)
                objects[cls][thing.id] = o
                getattr(m, name).append(o)
                if cls is Unit:
                    o.home = objects[Building][thing.home_id]
        return m

    def announce_waiting(self):
        """Alert the players on this map how many players they are waiting
        for."""
        c = EntryPoint.query(location=self, occupant=None).count()
        if c:
            self.broadcast(
                f'You are waiting for {c} {pluralise(c, "player")}.',
                sound='join.wav'
            )
        else:
            self.finalise()

    def valid_coordinates(self, x, y):
        """Return True if the given x and y coordinates are valid."""
        return x >= 0 and x <= self.size_x and y >= 0 and y <= self.size_y

    def delete(self):
        """Delete this map and everything on it."""
        assert not self.players, 'Cannot delete with players still present.'
        for name in ('buildings', 'features', 'units', 'entry_points'):
            for thing in getattr(self, name):
                thing.delete()
        super().delete()

    def random_coordinates(self):
        """Return random coordinates on this map."""
        x = randint(0, self.size_x)
        y = randint(0, self.size_y)
        return x, y

    @classmethod
    def create_random(
        cls, name, players, min_resource, max_resource, features
    ):
        """Create and return a randomly generated map.

        The map wich is created will necessarily already be saved, as will all
        objects created with it.

        Arguments:
        players: The maximum number of players who should be able to play the
        eventual map.
        min_resource: The minimum resource amount in each randomly-generated
        Feature instance.
        max_resource: The maximum resource amount in each randomly-generated
        Feature instance.
        features: A dictionary of type: number pairs, where type is a
        FeatureType instance, and number is the number of features of the given
        type to create.
        """
        self = cls(name=name, template=False)
        self.save()
        t = options.start_building
        for x in range(players):
            e = self.add_entry_point(*self.random_coordinates())
            e.save()
            self.add_building(t, e.x, e.y).save()
        for type, number in features.items():
            for x in range(number):
                f = self.add_feature(type, *self.random_coordinates())
                for name in f.type.resources:
                    setattr(f, name, randint(min_resource, max_resource))
                f.save()
        return self

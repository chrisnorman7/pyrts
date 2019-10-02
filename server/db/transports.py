"""Provides the Transport class."""

from time import time

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from twisted.internet import reactor

from .base import Base, LocationMixin


class Transport(Base, LocationMixin):
    """A destination for a unit."""

    __tablename__ = 'transports'
    destination_id = Column(
        Integer, ForeignKey('buildings.id'), nullable=True
    )
    destination = relationship(
        'Building', backref=backref(
            'incoming', cascade='delete, delete-orphan'
        )
    )
    land_time = Column(Integer, nullable=True)

    def add_passenger(self, unit):
        """Add a unit to self.passengers, and remove the given unit from the
        map."""
        unit.sound('board.wav')
        unit.location = None
        unit.onboard = self
        unit.save()

    def remove_passenger(self, unit):
        """Remove a unit from self.passengers and move it back to the map."""
        unit.onboard_id = None
        unit.location_id = self.location_id
        unit.move(*self.unit.coordinates)
        unit.sound('disembark.wav')
        unit.save()

    def launch(self):
        """Remove self.unit from self.location, and schedule a landing."""
        self.unit.sound('launch.wav')
        self.unit.location = None
        duration = self.unit.type.speed * self.unit.distance_to(
            self.destination
        )
        self.land_time = time() + duration
        reactor.callLater(duration, type(self).land, self.id)

    @classmethod
    def land(cls, id):
        """Land this unit, assuming the landing field still exists."""
        self = cls.get(id)
        if self is None:
            return  # Destroyed.
        self.unit.location = self.location
        self.unit.coordinates = self.destination.coordinates
        self.unit.sound('land.wav')

    def delete(self):
        """Delete all passengers."""
        for p in self.passengers:
            p.delete()
        return super().delete()

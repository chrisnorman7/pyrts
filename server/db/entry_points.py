"""Provides the EntryPoint class."""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref

from .base import Base, CoordinatesMixin, LocationMixin


class EntryPoint(Base, CoordinatesMixin, LocationMixin):
    """An entry point for players."""

    __tablename__ = 'entry_points'
    occupant_id = Column(Integer, ForeignKey('players.id'), nullable=True)
    occupant = relationship(
        'Player', backref=backref('entry_point', uselist=False)
    )

    def __str__(self):
        if self.occupant is None:
            owner = 'Empty'
        else:
            owner = self.occupant.name
        index = self.location.entry_points.index(self) + 1
        return f'Entry point {index} [{owner}]'

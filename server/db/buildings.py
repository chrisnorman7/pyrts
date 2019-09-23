"""Provides the BuildingType and Building classes."""

from sqlalchemy import Column, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .base import (
    Base, NameMixin, CoordinatesMixin, ResistanceMixin, LocationMixin,
    OwnerMixin, ResourcesMixin, TypeMixin, SoundMixin, MaxHealthMixin,
    HealthMixin, GetNameMixin
)


class BuildingRecruit(Base, ResourcesMixin):
    """Provides a link betwene building and unit types, allowing buildings
    to provide units. Resources are used during reruitment."""

    __tablename__ = 'building_recruits'
    building_type_id = Column(
        Integer, ForeignKey('building_types.id'), nullable=False
    )
    unit_type_id = Column(
        Integer, ForeignKey('unit_types.id'), nullable=False
    )
    pop_time = Column(Integer, nullable=False, default=4)


class BuildingType(
    Base, NameMixin, ResistanceMixin, ResourcesMixin, SoundMixin,
    MaxHealthMixin
):
    """A type of building. Resources are used during construction."""

    __tablename__ = 'building_types'
    homely = Column(Boolean, nullable=False, default=False)
    depends_id = Column(
        Integer, ForeignKey('building_types.id'), nullable=True
    )
    depends = relationship(
        'BuildingType', foreign_keys=[depends_id], backref='dependencies',
        remote_side='BuildingType.id'
    )
    recruits = relationship(
        'UnitType', backref='recruiters', secondary=BuildingRecruit.__table__
    )

    def get_pop_time(self, unit_type):
        """Get the pop time for the given UnitType instance."""
        return BuildingRecruit.one(
            building_type_id=self.id, unit_type_id=unit_type.id
        ).pop_time

    def set_pop_time(self, unit_type, value):
        """Set the pop time for the given UnitType instance to the given
        value."""
        BuildingRecruit.query(
            building_type_id=self.id, unit_type_id=unit_type.id
        ).update(
            {BuildingRecruit.pop_time: value}
            )

    def add_recruit(self, type, **resources):
        """Add the given UnitType instance as a recruit of this building
        type. It will cost the provided resources to recruit."""
        return BuildingRecruit(
            unit_type_id=type.id, building_type_id=self.id, **resources
        )

    def get_recruit(self, type):
        """Return the BuildingRecruit instance that represents the given
        UnitType instance."""
        return BuildingRecruit.one(
            building_type_id=self.id, unit_type_id=type.id
        )


class Building(
    Base, CoordinatesMixin, LocationMixin, OwnerMixin, TypeMixin,
    ResourcesMixin, HealthMixin, GetNameMixin
):
    """A building on a map. Resources are used for storage."""

    __tablename__ = 'buildings'
    __type_class__ = BuildingType

    def get_full_name(self):
        if self.owner is None:
            owner = 'Unclaimed'
        else:
            owner = str(self.owner)
        return f'{self.get_name()} ({owner})'

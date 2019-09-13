"""Provides the BuildingType and Building classes."""

from sqlalchemy import Column, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .base import (
    Base, NameMixin, CoordinatesMixin, ResistanceMixin, LocationMixin,
    OwnerMixin, ResourcesMixin, TypeMixin, SoundMixin, GetNameMixin,
    MaxHealthMixin, HealthMixin
)


class BuildingMobile(Base, ResourcesMixin):
    """Provides a link betwene building and mobile types, allowing buildings
    to provide mobiles. Resources are used during reruitment."""

    __tablename__ = 'building_mobiles'
    building_type_id = Column(
        Integer, ForeignKey('building_types.id'), nullable=False
    )
    mobile_type_id = Column(
        Integer, ForeignKey('mobile_types.id'), nullable=False
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
        'MobileType', backref='recruiters', secondary=BuildingMobile.__table__
    )

    def get_pop_time(self, mobile_type):
        """Get the pop time for the given MobileType instance."""
        return BuildingMobile.one(
            building_type_id=self.id, mobile_type_id=mobile_type.id
        ).pop_time

    def set_pop_time(self, mobile_type, value):
        """Set the pop time for the given MobileType instance to the given
        value."""
        BuildingMobile.query(
            building_type_id=self.id, mobile_type_id=mobile_type.id
        ).update(
            {BuildingMobile.pop_time: value}
            )

    def add_recruit(self, type, **resources):
        """Add the given MobileType instance as a recruit of this building
        type. It will cost the provided resources to recruit."""
        return BuildingMobile(
            mobile_type_id=type.id, building_type_id=self.id, **resources
        )

    def get_recruit(self, type):
        """Return the BuildingMobile instance that represents the given
        MobileType instance."""
        return BuildingMobile.one(
            building_type_id=self.id, mobile_type_id=type.id
        )


class Building(
    Base, CoordinatesMixin, LocationMixin, OwnerMixin, TypeMixin,
    ResourcesMixin, GetNameMixin, HealthMixin
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

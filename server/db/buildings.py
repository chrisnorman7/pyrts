"""Provides the BuildingType and Building classes."""

from sqlalchemy import Column, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .base import (
    Base, NameMixin, CoordinatesMixin, ResistanceMixin, LocationMixin,
    OwnerMixin, ResourcesMixin, TypeMixin, SoundMixin, GetNameMixin
)


class BuildingMobile(Base, ResourcesMixin):
    """Provides a link betwene building and mobile types, allowing buildings
    to provide mobiles."""

    __tablename__ = 'building_mobiles'
    building_type_id = Column(
        Integer, ForeignKey('building_types.id'), nullable=False
    )
    mobile_type_id = Column(
        Integer, ForeignKey('mobile_types.id'), nullable=False
    )
    pop_time = Column(Integer, nullable=False, default=4)


class BuildingType(
    Base, NameMixin, ResistanceMixin, ResourcesMixin, SoundMixin
):
    """A type of building."""

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
    build_time = Column(Integer, nullable=False, default=10)

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


class Building(
    Base, CoordinatesMixin, LocationMixin, OwnerMixin, TypeMixin,
    ResourcesMixin, GetNameMixin
):
    """A building on a map."""

    __tablename__ = 'buildings'
    __type_class__ = BuildingType

    def get_full_name(self):
        if self.owner is None:
            owner = 'Unclaimed'
        else:
            owner = str(self.owner)
        return f'{self.get_name()} ({owner})'

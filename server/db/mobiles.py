"""Provides the MobileType and Mobile classes."""

from sqlalchemy import Column, Boolean, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from .base import (
    Base, NameMixin, CoordinatesMixin, ResistanceMixin, LocationMixin,
    OwnerMixin, TypeMixin, SoundMixin, GetNameMixin, ResourcesMixin
)


class BuildingBuilder(Base):
    """Provides a link betwene building and mobile types, allowing mobiles to
    build buildings."""

    __tablename__ = 'building_builders'
    building_type_id = Column(
        Integer, ForeignKey('building_types.id'), nullable=False
    )
    mobile_type_id = Column(
        Integer, ForeignKey('mobile_types.id'), nullable=False
    )


class MobileType(Base, NameMixin, ResistanceMixin, SoundMixin, ResourcesMixin):
    """A type of mobile."""

    __tablename__ = 'mobile_types'
    strength = Column(Integer, nullable=False, default=1)
    can_build = relationship(
        'BuildingType', backref='builders', secondary=BuildingBuilder.__table__
    )


class Mobile(
    Base, CoordinatesMixin, LocationMixin, OwnerMixin, TypeMixin, GetNameMixin
):
    """A mobile on a map."""

    __tablename__ = 'mobiles'
    __type_class__ = MobileType
    home_id = Column(Integer, ForeignKey('buildings.id'), nullable=True)
    home = relationship('Building', backref='mobiles')
    selected = Column(Boolean, nullable=False, default=False)
    exploiting_class = Column(String(20), nullable=True)
    exploiting_id = Column(Integer, nullable=True)

    @property
    def exploiting(self):
        if self.exploiting_class is not None:
            return Base._decl_class_registry[self.exploiting_class].get(
                self.exploiting_id
            )

    @exploiting.setter
    def exploiting(self, value):
        self.exploiting_class = type(value).__name__
        self.exploiting_id = value.id

    def get_full_name(self):
        if self.owner is None:
            owner = 'Unemployed'
        else:
            owner = f'employed by {self.owner.name}'
        return f'{self.get_name()} [{owner}]'

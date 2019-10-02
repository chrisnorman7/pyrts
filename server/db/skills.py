"""Provides the SkillType and Skill classes, along with the SkillTypes
enumeration."""

from enum import Enum as _Enum

from sqlalchemy import Column, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship, backref

from .base import Base, ResourcesMixin


class SkillTypes(_Enum):
    """The possible skill types."""

    double_exploit = 'Improved materials gathering'
    tripple_exploit = 'Expert materials gathering'
    random_resurrect = 'Basic resurrection'
    specific_resurrect = 'Advanced resurrection'
    switch_sides = 'Turncoat spell'


class SkillType(Base, ResourcesMixin):
    """A skill which can be attached to a BuildingType instance for purchasing.
    Resources are used for purchasing."""

    __tablename__ = 'skill_types'
    skill_type = Column(Enum(SkillTypes), nullable=False)
    pop_time = Column(Integer, nullable=False, default=4)
    building_type_id = Column(
        Integer, ForeignKey('building_types.id'), nullable=False
    )
    building_type = relationship(
        'BuildingType', backref='skill_types', single_parent=True,
        cascade='all, delete-orphan'
    )


class Skill(Base):
    """Used to attach SkillTypes members to Building instances."""

    __tablename__ = 'skills'
    skill_type = Column(Enum(SkillTypes), nullable=False)
    building_id = Column(Integer, ForeignKey('buildings.id'), nullable=False)
    building = relationship(
        'Building', backref=backref('skills', cascade='all, delete-orphan'),
        single_parent=True
    )

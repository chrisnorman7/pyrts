"""Provides the SkillType and Skill classes, along with the SkillTypes
enumeration."""

from enum import Enum as _Enum
from random import choice

from sqlalchemy import Column, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship, backref

from .base import Base, ResourcesMixin
from .units import UnitType

from ..events import listen, on_exploit, on_kill


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
        'BuildingType', backref=backref(
            'skill_types', cascade='all, delete-orphan'
        ), single_parent=True
    )

    def get_name(self):
        return self.skill_type.name


class Skill(Base):
    """Used to attach SkillTypes members to Building instances."""

    __tablename__ = 'skills'
    skill_type = Column(Enum(SkillTypes), nullable=False)
    building_id = Column(Integer, ForeignKey('buildings.id'), nullable=False)
    building = relationship(
        'Building', backref=backref(
            'skills', cascade='delete, delete-orphan'
        ), single_parent=True
    )


@listen(on_exploit)
def check_exploit_skills(action):
    """Check to see if action.unit.home has either of te exploit skills
    assigned."""
    o = action.unit.owner
    if o is None:
        return  # Nothing to do.
    elif o.has_skill(SkillTypes.tripple_exploit):
        multiplier = 3
    elif o.has_skill(SkillTypes.double_exploit):
        multiplier = 2
    else:
        multiplier = 1
    action.amount *= multiplier


@listen(on_kill)
def check_resurrect_skills(unit, target):
    """Check to see if we should be resurrecting target."""
    o = target.owner
    if o is None:
        return  # Nothing to do.
    elif o.has_skill(SkillTypes.specific_resurrect):
        ut = target.type
    elif o.has_skill(SkillTypes.random_resurrect):
        ut = choice(UnitType.all())
    else:
        return
    u = target.location.add_unit(ut, *target.coordinates)
    u.health = 0
    u.owner = o
    u.home = target.home
    u.save()
    o.message(f'{u.get_name()} is ready.')

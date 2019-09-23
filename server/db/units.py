"""Provides the UnitType and Unit classes."""

import os.path
from enum import Enum as _Enum
from random import uniform, choice

from sqlalchemy import Column, Boolean, Integer, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from twisted.internet import reactor
from twisted.internet.error import AlreadyCancelled, AlreadyCalled

from .base import (
    Base, NameMixin, CoordinatesMixin, ResistanceMixin, LocationMixin,
    OwnerMixin, TypeMixin, SoundMixin, ResourcesMixin, MaxHealthMixin,
    HealthMixin, GetNameMixin, StrengthMixin
)

from ..exc import NoSuchSound

tasks = {}


class UnitActions(_Enum):
    """The next action to take."""
    exploit = 0
    drop = 1
    patrol_out = 2
    patrol_back = 3
    travel = 4
    repair = 5
    guard = 6


class BuildingBuilder(Base):
    """Provides a link betwene building and unit types, allowing units to
    build buildings."""

    __tablename__ = 'building_builders'
    building_type_id = Column(
        Integer, ForeignKey('building_types.id'), nullable=False
    )
    unit_type_id = Column(
        Integer, ForeignKey('unit_types.id'), nullable=False
    )


class UnitType(
    Base, NameMixin, ResistanceMixin, SoundMixin, ResourcesMixin,
    MaxHealthMixin, StrengthMixin
):
    """A type of unit. Resources are used to decide which resources can be
    exploited by units of this type."""

    __tablename__ = 'unit_types'
    can_build = relationship(
        'BuildingType', backref='builders', secondary=BuildingBuilder.__table__
    )
    speed = Column(Integer, nullable=False, default=8)
    auto_repair = Column(Boolean, nullable=False, default=False)
    repair_amount = Column(Integer, nullable=False, default=1)
    attack_type_id = Column(
        Integer, ForeignKey('attack_types.id'), nullable=True
    )
    attack_type = relationship('AttackType', backref='units')

    def add_building(self, type):
        """Add a BuildingType instance that can be built by units of this
        type."""
        return BuildingBuilder(
            unit_type_id=self.id, building_type_id=type.id
        )

    def get_building(self, type):
        """Return the BuildingBuilder instance associated with this unit
        type, and the provided BuildingType instance."""
        return BuildingBuilder.one(
            unit_type_id=self.id, building_type_id=type.id
        )


class Unit(
    Base, CoordinatesMixin, LocationMixin, OwnerMixin, TypeMixin, HealthMixin,
    ResourcesMixin, GetNameMixin
):
    """A unit on a map. Resources are used for storage (carrying)."""

    __tablename__ = 'units'
    __type_class__ = UnitType
    home_id = Column(Integer, ForeignKey('buildings.id'), nullable=True)
    home = relationship('Building', backref='units')
    selected = Column(Boolean, nullable=False, default=False)
    exploiting_class = Column(String(20), nullable=True)
    exploiting_id = Column(Integer, nullable=True)
    exploiting_material = Column(String(20), nullable=True)
    # If self.action is None, this unit is considered to be standing around
    # doing nothing.
    action = Column(Enum(UnitActions), nullable=True)
    target_x = Column(Integer, nullable=False, default=0)
    target_y = Column(Integer, nullable=False, default=0)

    @property
    def exploiting(self):
        if self.exploiting_class is not None:
            return Base._decl_class_registry[self.exploiting_class].get(
                self.exploiting_id
            )

    @exploiting.setter
    def exploiting(self, value):
        if value is None:
            class_name = None
            id = None
        else:
            class_name = type(value).__name__
            id = value.id
        self.exploiting_class = class_name
        self.exploiting_id = id

    @property
    def target(self):
        return self.target_x, self.target_y

    @target.setter
    def target(self, value):
        self.target_x, self.target_y = value

    def get_full_name(self):
        """Get this unit's name, and the name of their employer (if any)."""
        if self.owner is None:
            owner = 'Unemployed'
        else:
            owner = f'employed by {self.owner.name}'
        return f'{self.get_name()} [{owner}]'

    def kill_task(self):
        """Get any task for this unit and kill it, to prevent duplicate
        tasks."""
        t = tasks.pop(self.id, None)
        try:
            t.cancel()
        except (AlreadyCancelled, AlreadyCalled, AttributeError):
            pass  # Already cancelled or non existant.

    def random_speed(self):
        """Return a random speed between 0.0 and self.type.speed."""
        return uniform(0.0, self.type.speed)

    def start_task(self):
        """Start a task for this unit."""
        self.kill_task()
        tasks[self.id] = reactor.callLater(self.random_speed(), self.progress)

    def sound(self, path):
        """Make this object emit a sound."""
        # We need to hack out the Player class because Unit is imported in
        # players.py.
        Player = Base._decl_class_registry['Player']
        for player in Player.all(location=self.location, x=self.x, y=self.y):
            player.sound(path)

    def move(self, x, y):
        """Move this unit and make a sound."""
        sound = f'static/sounds/move/{self.type.name}.wav'
        self.sound(sound)
        self.coordinates = x, y
        self.save()
        self.sound(sound)

    def move_towards(self, tx, ty):
        """Move towards a particular set of coordinates."""
        x, y = self.coordinates
        if tx < x:
            x -= 1
        elif tx > x:
            x += 1
        if ty < y:
            y -= 1
        elif ty > y:
            y += 1
        self.move(x, y)

    def exploit(self, feature, material):
        """Start exploiting a Feature f."""
        self.exploiting = feature
        self.target = feature.coordinates
        self.action = UnitActions.exploit
        self.exploiting_material = material
        self.start_task()

    def repair(self, building):
        """Repair the given building. The reference will be stored on
        self.exploiting."""
        self.action = UnitActions.repair
        self.exploiting = building
        self.start_task()

    def travel(self, x, y):
        """Start this unit travelling."""
        self.target = x, y
        self.exploiting = None
        self.action = UnitActions.travel
        self.start_task()

    def guard(self):
        """Guard the current coordinates."""
        self.kill_task()
        self.action = UnitActions.guard

    def patrol(self, x, y):
        """Start this unit patrolling."""
        self.target = (x, y)
        self.action = UnitActions.patrol_out
        self.start_task()

    def action_description(self):
        """Return a string describing what this unit is up to."""
        a = self.action
        if a is None:
            return 'doing nothing'
        elif a is UnitActions.guard:
            return f'guarding {self.coordinates}'
        elif a is UnitActions.exploit:
            x = self.exploiting
            if x is None:
                return 'exploiting a non-existant resource'
            else:
                return f'exploiting {x.get_name()}'
        elif a is UnitActions.drop:
            h = self.home
            if h is None:
                return 'attempting to deliver resources'
            else:
                return f'delivering resources to {h.get_name()}'
        elif a is UnitActions.travel:
            return f'travelling to {self.target}'
        elif a in (UnitActions.patrol_out, UnitActions.patrol_back):
            h = self.home
            if h is None:
                h = 'nowhere'
            else:
                h = h.coordinates
            return f'patrolling between {self.target} and {h}'
        elif a is UnitActions.repair:
            if self.exploiting is None:
                name = 'nothing'
            else:
                name = self.exploiting.get_name()
            return f'repairing {name}'
        else:
            return str(a)

    def reset_action(self):
        """Returns this unit to its default state."""
        self.action = None
        self.exploiting = None
        self.exploiting_material = None
        self.target = self.coordinates

    def rehome(self):
        """In the event that self.home becomes None, try and find a new
        home."""
        Building = Base._decl_class_registry['Building']
        BuildingType = Base._decl_class_registry['BuildingType']
        self.home = Building.query(
            location=self.location, owner=self.owner
        ).join(
            Building.type
        ).filter(BuildingType.homely.is_(True)).first()

    def declair_homeless(self):
        """This unit is homeless. Tell the world."""
        return self.speak('I am homeless')

    def progress(self):
        """Progress this object through whatever task it is performing."""
        Building = Base._decl_class_registry['Building']
        a = self.action
        if self.owner is None:
            # Stop what we are doing while unemployed.
            return self.reset_action()
        elif a is UnitActions.drop:
            if self.home is None:
                # Homeless now. Try and reroute.
                self.rehome()
                if self.home is None:
                    # They have no buildings left, we are probably unemployed.
                    self.declair_homeless()
                    return self.reset_action()
            elif self.coordinates == self.home.coordinates:
                # We are home, drop off some exploited material.
                for name in self.resources:
                    value = getattr(self, name)
                    setattr(self, name, 0)
                    setattr(self.home, name, getattr(self.home, name) + value)
                self.sound('static/sounds/drop.wav')
                self.action = UnitActions.exploit
            else:
                self.move_towards(*self.home.coordinates)
        elif a is UnitActions.exploit:
            if self.coordinates == self.target:
                # We are in place.
                name = self.exploiting_material
                x = self.exploiting
                if x is None:
                    # Not exploiting anymore.
                    self.speak('Nothing there')
                    return self.reset_action()
                value = getattr(x, name)
                if not value:
                    # Empty resource.
                    self.speak('Finished')
                    return self.reset_action()
                self.sound(f'static/sounds/exploit/{name}.wav')
                setattr(self, name, 1)
                value -= 1
                setattr(x, name, value)
                self.action = UnitActions.drop
            else:
                self.move_towards(*self.target)
        elif a is UnitActions.patrol_out:
            if self.coordinates == self.target:
                self.action = UnitActions.patrol_back
            else:
                self.move_towards(*self.target)
        elif a is UnitActions.patrol_back:
            if self.home is None:
                self. rehome()
                if self.home is None:
                    self.declair_homeless()
                    return self.reset_action()
            elif self.coordinates == self.home.coordinates:
                self.action = UnitActions.patrol_out
            else:
                self.move_towards(*self.home.coordinates)
        elif a is UnitActions.travel:
            if self.coordinates == self.target:
                self.speak('Here I am')
                return self.reset_action()  # Done.
            else:
                self.move_towards(*self.target)
        elif a is UnitActions.repair:
            x = self.exploiting
            if x is None or x.health is None:
                # We are done.
                return self.reset_action()
            elif self.coordinates == x.coordinates:
                # We are here, do the repair.
                x.heal(self.type.repair_amount)
                self.sound('static/sounds/repair.wav')
                x.save()
                if x.health is None:
                    self.speak('Finished')
            else:
                self.move_towards(*x.coordinates)
        elif a is UnitActions.guard:
            if self.type.auto_repair:
                q = Building.all(
                    Building.health.isnot(None),
                    **self.owner.same_coordinates()
                )
                if len(q):
                    b = choice(q)
                    b.heal(self.type.repair_amount)
                    self.sound('static/sounds/repair.wav')
                    if b.health is None:
                        self.speak('Finished')
        else:
            return self.reset_action()  # No action.
        self.save()  # Better save since we might be inside a deferred.
        self.start_task()

    def speak(self, text):
        """If text has a wave file associated with it, then play the sound.
        Otherwise use text."""
        sound = f'static/sounds/speech/{text}.wav'
        if not os.path.isfile(sound):
            raise NoSuchSound(sound)
        if self.owner is None:
            owner_player = False
        elif self.owner.coordinates == self.coordinates:
            owner_player = False
        else:
            owner_player = True
        if owner_player:
            self.owner.sound(sound)
        return self.sound(sound)
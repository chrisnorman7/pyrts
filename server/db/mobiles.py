"""Provides the MobileType and Mobile classes."""

from enum import Enum as _Enum
from random import uniform, randint

from sqlalchemy import Column, Boolean, Integer, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from twisted.internet import reactor
from twisted.internet.error import AlreadyCancelled

from .base import (
    Base, NameMixin, CoordinatesMixin, ResistanceMixin, LocationMixin,
    OwnerMixin, TypeMixin, SoundMixin, GetNameMixin, ResourcesMixin,
    MaxHealthMixin, HealthMixin
)

tasks = {}


class MobileActions(_Enum):
    """The next action to take."""
    exploit = 0
    drop = 1
    patrol_out = 2
    patrol_back = 3
    travel = 4
    repair = 5
    guard = 6


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


class MobileType(
    Base, NameMixin, ResistanceMixin, SoundMixin, ResourcesMixin,
    MaxHealthMixin
):
    """A type of mobile. Resources are used to decide which resources can be
    exploited by mobiles of this type."""

    __tablename__ = 'mobile_types'
    strength = Column(Integer, nullable=False, default=1)
    can_build = relationship(
        'BuildingType', backref='builders', secondary=BuildingBuilder.__table__
    )
    speed = Column(Integer, nullable=False, default=8)

    def add_building(self, type):
        """Add a BuildingType instance that can be built by mobiles of this
        type."""
        return BuildingBuilder(
            mobile_type_id=self.id, building_type_id=type.id
        )

    def get_building(self, type):
        """Return the BuildingBuilder instance associated with this mobile
        type, and the provided BuildingType instance."""
        return BuildingBuilder.one(
            mobile_type_id=self.id, building_type_id=type.id
        )


class Mobile(
    Base, CoordinatesMixin, LocationMixin, OwnerMixin, TypeMixin, GetNameMixin,
    HealthMixin, ResourcesMixin
):
    """A mobile on a map. Resources are used for storage (carrying)."""

    __tablename__ = 'mobiles'
    __type_class__ = MobileType
    home_id = Column(Integer, ForeignKey('buildings.id'), nullable=True)
    home = relationship('Building', backref='mobiles')
    selected = Column(Boolean, nullable=False, default=False)
    exploiting_class = Column(String(20), nullable=True)
    exploiting_id = Column(Integer, nullable=True)
    exploiting_material = Column(String(20), nullable=True)
    # If self.action is None, this mobile is considered to be standing around
    # doing nothing.
    action = Column(Enum(MobileActions), nullable=True)
    repair_amount = Column(Integer, nullable=False, default=1)
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
        if self.owner is None:
            owner = 'Unemployed'
        else:
            owner = f'employed by {self.owner.name}'
        return f'{self.get_name()} [{owner}]'

    def kill_task(self):
        """Get any task for this mobile and kill it, to prevent duplicate
        tasks."""
        t = tasks.pop(self.id, None)
        try:
            t.cancel()
        except (AlreadyCancelled, AttributeError):
            pass  # Already cancelled or non existant.

    def random_speed(self):
        """Return a random speed between 0.0 and self.type.speed."""
        return uniform(0.0, self.type.speed)

    def start_task(self):
        """Start a task for this mobile."""
        self.kill_task()
        reactor.callLater(self.random_speed(), self.progress)

    def sound(self, path):
        """Make this object emit a sound."""
        # We need to hack out the Player class because Mobile is imported in
        # players.py.
        Player = Base._decl_class_registry['Player']
        for player in Player.all(location=self.location, x=self.x, y=self.y):
            player.sound(path)

    def move(self, x, y):
        """Move this mobile and make a sound."""
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
        self.action = MobileActions.exploit
        self.exploiting_material = material
        self.start_task()

    def repair(self, building):
        """Repair the given building. The reference will be stored on
        self.exploiting."""
        self.action = MobileActions.repair
        self.exploiting = building
        self.start_task()

    def travel(self, x, y):
        """Start this mobile travelling."""
        self.target = x, y
        self.exploiting = None
        self.action = MobileActions.travel
        self.start_task()

    def guard(self):
        """Guard the current coordinates."""
        self.kill_task()
        self.action = MobileActions.guard

    def patrol(self, x, y):
        """Start this mobile patrolling."""
        self.target = (x, y)
        self.action = MobileActions.patrol_out
        self.start_task()

    def action_description(self):
        """Return a string describing what this mobile is up to."""
        a = self.action
        if a is MobileActions.guard:
            return f'guarding {self.coordinates}'
        elif a is MobileActions.exploit:
            x = self.exploiting
            if x is None:
                return 'exploiting a non-existant resource'
            else:
                return f'exploiting {x.get_name()}'
        elif a is MobileActions.drop:
            h = self.home
            if h is None:
                return 'attempting to deliver resources'
            else:
                return f'delivering resources to {h.get_name()}'
        elif a is MobileActions.travel:
            return f'travelling to {self.target}'
        elif a in (MobileActions.patrol_out, MobileActions.patrol_back):
            h = self.home
            if h is None:
                h = 'nowhere'
            else:
                h = h.coordinates
            return f'patrolling between {self.target} and {h}'
        else:
            return str(a)

    def progress(self):
        """Progress this object through whatever task it is performing."""
        self.kill_task()
        Building = Base._decl_class_registry['Building']
        BuildingType = Base._decl_class_registry['BuildingType']
        a = self.action
        if self.owner is None:
            return  # Stop what we are doing while unemployed.
        elif a is MobileActions.drop:
            if self.home is None:
                # Homeless now. Try and reroute.
                self.home = Building.query(owner_id=self.owner_id).join(
                    Building.type
                ).filter(BuildingType.homely.is_(True)).first()
                if self.home is None:
                    # They have no buildings left, we are probably unemployed.
                    self.owner.message(
                        f'Cannot find a home for {self.get_name()} to deliver '
                        'resources.'
                    )
                    return
            elif self.coordinates == self.home.coordinates:
                # We are home, drop off some exploited material.
                for name in self.resources:
                    value = getattr(self, name)
                    setattr(self, name, 0)
                    setattr(self.home, name, getattr(self.home, name) + value)
                self.sound('static/sounds/drop.wav')
                self.action = MobileActions.exploit
            else:
                self.move_towards(*self.home.coordinates)
        elif a is MobileActions.exploit:
            if self.coordinates == self.target:
                # We are in place.
                name = self.exploiting_material
                x = self.exploiting
                if x is None:
                    self.action = None
                    return  # Not exploiting anymore.
                value = getattr(x, name)
                if not value:
                    self.owner.message(f'{x.get_name()} exhausted.')
                    return  # Empty resource.
                self.sound(f'static/sounds/exploit/{name}.wav')
                setattr(self, name, 1)
                value -= 1
                setattr(x, name, value)
                if not value:
                    self.exploiting = None
                self.action = MobileActions.drop
            else:
                self.move_towards(*self.target)
        elif a is MobileActions.patrol_out:
            if self.coordinates == self.target:
                self.action = MobileActions.patrol_back
            else:
                self.move_towards(*self.target)
        elif a is MobileActions.patrol_back:
            if self.home is None:
                self.action = None
                self.owner.message(
                    f'{self.get_name()} has nowhere to patrol back to.'
                )
                return  # Homeless.
            elif self.coordinates == self.home.coordinates:
                self.action = MobileActions.patrol_out
            else:
                self.move_towards(*self.home.coordinates)
        elif a is MobileActions.travel:
            if self.coordinates == self.target:
                self.action = None
                self.owner.message(
                    f'{self.get_name()} has arrived at {self.coordinates}.'
                )
                return  # Done.
            else:
                self.move_towards(*self.target)
        elif a is MobileActions.repair:
            x = self.exploiting
            if x is None or x.health is None:
                # We are done.
                self.action = None
                self.exploiting = None
                return
            if self.coordinates == x.coordinates:
                # We are here, do the repair.
                x.heal(randint(0, self.repair_amount))
                self.sound('static/sounds/repair.wav')
                x.save()
                if x.health is None:
                    self.owner.message(f'{x.get_name()} has been repaired.')
            else:
                self.move_towards(*x.coordinates)
        else:
            return  # No action.
        self.save()  # Better save since we might be inside a deferred.
        reactor.callLater(self.random_speed(), self.progress)

"""Provides the MobileType and Mobile classes."""

from enum import Enum as _Enum

from sqlalchemy import Column, Boolean, Integer, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from twisted.internet import reactor

from .base import (
    Base, NameMixin, CoordinatesMixin, ResistanceMixin, LocationMixin,
    OwnerMixin, TypeMixin, SoundMixin, GetNameMixin, ResourcesMixin
)


class MobileActions(_Enum):
    """The next action to take."""
    exploit = 0
    drop = 1
    patrol_out = 2
    patrol_back = 3


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
    speed = Column(Integer, nullable=False, default=3)


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
    exploiting_material = Column(String(20), nullable=True)
    # If self.action is None, this mobile is considered to be standing around
    # doing nothing.
    action = Column(Enum(MobileActions), nullable=True)
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
        self.exploiting_class = type(value).__name__
        self.exploiting_id = value.id

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
        """Start explotoing a Feature f."""
        self.exploiting = feature
        self.target = feature.coordinates
        self.action = MobileActions.exploit
        self.exploiting_material = material
        reactor.callLater(self.type.speed, self.progress)

    def progress(self):
        """Progress this object through whatever task it is performing."""
        a = self.action
        if self.owner is None:
            return  # Stop what we are doing while unemployed.
        elif a is MobileActions.drop:
            if self.home is None:
                # Homeless now. Try and reroute.
                Building = Base._decl_class_registry['Building']
                self.home = Building.first(owner_id=self.owner_id)
                if self.home is None:
                    # They have no buildings left, we are probably unemployed.
                    return
            elif self.coordinates == self.home.coordinates:
                # We are home, drop off some exploited material.
                name = self.exploiting_material
                setattr(self.home, name, getattr(self.home, name) + 1)
                self.action = MobileActions.exploit
            else:
                self.move_towards(*self.home.coordinates)
        elif a is MobileActions.exploit:
            if self.coordinates == self.target:
                # We are in place.
                if self.exploiting is None:
                    # We have nothing to do. That resource is exhausted.
                    self.direction = None
                    return
                else:
                    name = self.exploiting_material
                    setattr(
                        self.exploiting, name,
                        getattr(self.exploiting, name) - 1
                    )
                    self.action = MobileActions.drop
            else:
                self.move_towards(*self.target)
        elif a is MobileActions.patrol_out:
            if self.coordinates == self.target:
                self.action = MobileActions.patrol_back
            else:
                self.move_towards(self.target)
        elif a is MobileActions.patrol_back:
            if self.home is None:
                self.action = None
                return  # Homeless.
            elif self.coordinates == self.home.coordinates:
                self.action = MobileActions.patrol_out
            else:
                self.move_towards(self.home)
        else:
            return  # No action.
        self.save()  # Better save since we might be inside a deferred.
        reactor.callLater(self.type.speed, self.progress)

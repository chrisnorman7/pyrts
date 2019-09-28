"""Provides the Player class."""

import os.path

from random import choice

from passlib.hash import sha512_crypt
from sqlalchemy import Column, Boolean, Integer, String, Float
from twisted.internet import reactor

from .base import Base, NameMixin, LocationMixin, CoordinatesMixin
from .buildings import Building, BuildingType
from .entry_points import EntryPoint
from .features import Feature
from .units import Unit

from ..exc import InvalidUsername, InvalidPassword, NoSuchSound
from ..options import options
from ..socials import factory
from ..util import pluralise

crypt = sha512_crypt.using(rounds=10000)
connections = {}


class Player(Base, NameMixin, CoordinatesMixin, LocationMixin):
    """A player."""

    __tablename__ = 'players'
    username = Column(String(25), nullable=False)
    password = Column(String(120), nullable=False)
    admin = Column(Boolean, nullable=False, default=False)
    connected = Column(Boolean, nullable=False, default=False)
    focussed_class = Column(String(20), nullable=True)
    focussed_id = Column(Integer, nullable=True)
    volume = Column(Float, nullable=False, default=0.05)
    code = Column(String(1000), nullable=True)

    @classmethod
    def create(cls, username, password, name):
        """Create a new user."""
        p = cls(username=username, name=name)
        p.set_password(password)
        return p

    @classmethod
    def authenticate(cls, username, password):
        """Return a Player object, or raise an exception."""
        p = cls.query(username=username).first()
        if p is None:
            raise InvalidUsername
        if p.check_password(password):
            return p
        raise InvalidPassword

    def set_password(self, password):
        """Give this player a new password."""
        self.password = crypt.hash(password)

    def check_password(self, password):
        """Check this player's password against the supplied password."""
        return crypt.verify(password, self.password)

    def send_volume(self):
        """Send self.volume to self.connection."""
        if self.connection is not None:
            self.connection.send('volume', self.volume)

    @property
    def connection(self):
        return connections.get(self.id, None)

    @connection.setter
    def connection(self, value):
        if value is None:
            del connections[self.id]
        else:
            old = self.connection
            if old is not None:
                old.message('Logging you in from somewhere else.')
                old.player_id = None
                old.send('disconnecting')
                old.transport.loseConnection()
            self.connected = True
            connections[self.id] = value
            value.authenticated(self)
            self.send_volume()
            if self.location is None:
                value.call_command('main_menu')
            else:
                value.message('You continue your game.')
                self.move(self.x, self.y)
                for player in self.neighbours:
                    player.message(f'{self.name} has returned.')

    def message(self, string):
        """Send a message to this player's connection."""
        if self.connection is None:
            return False
        self.connection.message(string)

    @property
    def neighbours(self):
        """Return the players in the same map as this player, excluding this
        player."""
        cls = type(self)
        return cls.query(
            cls.id != self.id, cls.location_id == self.location_id
        )

    def move(self, x, y):
        """Move this player to the given coordinates."""
        self.x = x
        self.y = y
        self.save()
        if self.connection is None:
            return  # No point in telling them stuff they can't see.
        self.connection.stop_loops()
        loops = []  # Only play unique loops.
        for obj in self.visible_objects:
            if isinstance(obj, (Feature, Building)):
                try:
                    sound = obj.type.sound
                    if sound not in loops:
                        loops.append(sound)
                        self.connection.start_loop(sound)
                except NoSuchSound:
                    pass
            self.message(obj.get_name())
        for ep in EntryPoint.all(x=self.x, y=self.y, location=self.location):
            self.message(str(ep))
        self.message('(%d, %d).' % (self.x, self.y))

    def do_social(
        self, string, perspectives=None, sound=None, local=False, **kwargs
    ):
        """Perform a social in the context of this player. If perspectives is a
        list, add it to a list containing this player, to form a full
        perspectives list."""
        if perspectives is None:
            perspectives = []
        perspectives.insert(0, self)
        strings = factory.get_strings(string, perspectives, **kwargs)
        filter_args = []
        if local:
            filter_kwargs = self.same_coordinates()
        else:
            filter_kwargs = dict(location=self.location)
        cls = type(self)
        for player in cls.query(*filter_args, **filter_kwargs):
            try:
                index = perspectives.index(player)
            except (ValueError, IndexError):
                index = -1
            player.message(strings[index])
            if sound is not None:
                player.sound(sound)

    @property
    def focussed_object(self):
        """Return the object this player is currently focussed on."""
        if self.focussed_class is None or self.focussed_id is None:
            return
        return Base._decl_class_registry[self.focussed_class].get(
            self.focussed_id
        )

    @focussed_object.setter
    def focussed_object(self, value):
        if value is None:
            self.focussed_class = None
            self.focussed_id = None
        else:
            self.focussed_class = type(value).__name__
            self.focussed_id = value.id

    def join_map(self, m):
        """Allow this player to join a Map instance m."""
        self.location = m
        e = choice(EntryPoint.all(location=m, occupant=None))
        e.occupant = self
        e.save()
        self.do_social('%1N join%1s the map at ({x}, {y}).', x=e.x, y=e.y)
        m.announce_waiting()
        b = Building.query(
            location=m, x=e.x, y=e.y, owner=None
        ).join(Building.type).filter(
            BuildingType.id == options.start_building.id
        ).first()
        if b is None:
            self.message('You are homeless.')
        else:
            b.owner = self
            b.save()
        self.move(e.x, e.y)
        self.send_title()
        self.save()

    def leave_map(self):
        """Leave the current map, relinquishing all assets."""
        self.entry_point = None
        self.do_social('%1N leave%1s the map.')
        loc = self.location
        self.location = None
        for cls in (Building, Unit):
            cls.query(location=loc, owner=self).update({cls.owner_id: None})
        if loc.finalised is None:
            if loc.players:
                loc.announce_waiting()
            elif not loc.template:
                loc.delete()
        else:
            if loc.players:
                loc.finalised = None
            else:
                loc.delete()
        if self.connection is not None:
            self.connection.send('stop_loops')
            self.send_title()
        self.save()

    @property
    def visible_objects(self):
        """Return a list of those objects that this player can see."""
        results = []
        kwargs = self.same_coordinates()
        for cls in (Player, Building, Feature, Unit):
            if cls is Player:
                args = [cls.id.isnot(self.id)]
            else:
                args = []
            results.extend(cls.all(*args, **kwargs))
        return results

    def sound(self, path):
        """Tell the client to play a sound. The URL will have options.base_url
        prepended."""
        if self.connection is None:
            return
        actual_path = os.path.join(options.sounds_path, path)
        if not os.path.isfile(actual_path):
            raise NoSuchSound(path)
        path += f'?{os.path.getmtime(actual_path)}'
        self.connection.logger.debug('Playing sound %s.', path)
        url = options.sounds_url + path
        self.connection.send('sound', url)

    def delete(self):
        """Delete this player, and disown all of its objects."""
        if self.location is not None:
            self.leave_map()
        super().delete()

    def disconnect(self):
        """Disconnect this player."""
        if self.connection is None:
            return False
        self.connection.transport.loseConnection()
        return True

    def get_full_name(self):
        connected = "connected" if self. connected else "disconnected"
        return f'{self.name} ({connected})'

    @property
    def selected_units(self):
        return Unit.query(owner=self, selected=True)

    def same_coordinates(self):
        """Return a set of query-ready args representing this player's current
        location and coordinates."""
        return dict(location=self.location, x=self.x, y=self.y)

    def deselect_units(self):
        """Deselect any selected units."""
        self.selected_units.update({Unit.selected: False})

    def call_later(self, time, *args, **kwargs):
        """Use reactor.callLater to schedule something, telling the player how
        long they have to wait."""
        reactor.callLater(time, *args, **kwargs)
        self.message(f'({time} {pluralise(time, "second")})')

    def send_title(self):
        """Send the title which should be used in the client's browser."""
        n = self.get_name()
        if self.location is not None:
            n += f' ({self.location.get_name()})'
        if self.connection is None:
            return False
        self.connection.send('title', f'{options.server_name} | {n}')
        return True

    @classmethod
    def message_admins(cls, string, sound='admin.wav'):
        """Send all connected admins the provided string."""
        for p in cls.all(admin=True, connected=True):
            p.sound(sound)
            p.message(string)

    def has_lost(self):
        """Return True if this player has lost the game. False otherwise."""
        if self.owned_buildings or self.owned_units:
            return False
        return True

    def has_won(self):
        """Return True if this player has won."""
        if not Building.count(Building.owner_id.isnot(self.id)) or \
           Unit.count(Unit.owner_id.isnot(self.id)):
            return True
        return False

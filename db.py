"""Database engine and tables."""

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, \
     Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from attrs_sqlalchemy import attrs_sqlalchemy
from config import db_url, db_echo
from objects import TYPE_FEATURE, TYPE_MOBILE, TYPE_BUILDING
from features import feature_types
from mobiles import mobile_types
from buildings import building_types

engine = create_engine(db_url, echo=db_echo)


class _Base:
    """Base for Base."""
    id = Column(Integer, primary_key=True)

    def save(self):
        """Save this object."""
        session.add(self)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e


Base = declarative_base(bind=engine, cls=_Base)
Session = sessionmaker(bind=engine)
session = Session()


@attrs_sqlalchemy
class Game(Base):
    """A game board."""
    __tablename__ = 'games'
    size_x = Column(Integer, nullable=False, default=30)
    size_y = Column(Integer, nullable=False, default=30)
    move_amount = Column(Float, nullable=False, default=1.0)

    def __str__(self):
        return 'Game %d' % self.id


@attrs_sqlalchemy
class Player(Base):
    """A Player."""
    __tablename__ = 'players'
    name = Column(String(50), unique=True, nullable=False)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=True)
    game = relationship('Game', backref='players')
    start_x = Column(Float, nullable=False, default=0.0)
    start_y = Column(Float, nullable=False, default=0.0)
    gold = Column(Integer, nullable=False, default=50)
    food = Column(Integer, nullable=False, default=50)
    wood = Column(Integer, nullable=False, default=50)
    water = Column(Integer, nullable=False, default=50)

    @property
    def connected(self):
        """Return True if this player is connected, False otherwise."""
        return hasattr(self, 'connection')

    def disconnect(self):
        """Disconnect this player."""
        if self.connected:
            self.connection.transport.loseConnection()
            return True
        else:
            return False

    def notify(self, string, *args, **kwargs):
        """Notify this player of something."""
        # Should probably use try-except here, but then we run the risk of me
        # changing the protocol and forgetting which method to use.
        if self.connected:
            self.connection.sendLine(string.format(*args, **kwargs).encode())

    def end_output(self):
        """Notify the client not to expect any further output."""
        self.notify('---')


@attrs_sqlalchemy
class GameObject(Base):
    """An object in the game."""
    __tablename__ = 'objects'
    name = Column(String(50), nullable=True)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False)
    game = relationship('Game', backref='objects')
    x = Column(Float, nullable=False, default=0.0)
    target_x = Column(Float, nullable=False, default=0.0)
    y = Column(Float, nullable=False, default=0.0)
    target_y = Column(Float, nullable=False, default=0.0)
    owner_id = Column(Integer, ForeignKey('players.id'), nullable=True)
    owner = relationship('Player', backref='owned_objects')
    hp = Column(Integer, nullable=True)
    mana = Column(Integer, nullable=True)
    type_flag = Column(Integer, nullable=False)
    type_parent = Column(String(20), nullable=False)

    @property
    def type(self):
        """Get the game type of this object."""
        dict = {
            TYPE_FEATURE: feature_types,
            TYPE_MOBILE: mobile_types,
            TYPE_BUILDING: building_types
        }[self.type_flag]
        return dict[self.type_parent]

    @type.setter
    def type(self, value):
        self.type_parent = value.name
        self.type_flag = value.type_flag
        if self.id is None:
            self.save()
        self.name = '%s %d' % (self.type.name, self.id)
        self.save()

    def move(self, x=None, y=None):
        """Move this object towards x and y if provided, otherwise the pre-
        existing target coordinates."""
        if self.type_flag != TYPE_MOBILE:
            raise RuntimeError('Cannot move something that is not a mobile.')
        if x is not None:
            self.target_x = x
        if y is not None:
            self.target_y = y


Base.metadata.create_all()

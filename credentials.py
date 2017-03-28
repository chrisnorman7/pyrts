"""User accounts and the like."""

from passlib import hash
from sqlalchemy.orm.exc import NoResultFound
import db
from config import password_crypt, password_rounds
from util import match


crypt = getattr(hash, password_crypt)


def create_player(username, password, name=None):
    """Create a new player."""
    p = db.Player(username=username)
    p.name = name or username
    set_password(p, password)
    return p


def set_password(player, password):
    """Set the password for the specified player to the specified value."""
    player.password = crypt.encrypt(password, rounds=password_rounds)
    player.save()


def verify(player, password):
    """Return True if player's password is the one provided."""
    return crypt.verify(password, player.password)


def authenticate(username, password):
    """Either return the player matching the specified credentials or None."""
    try:
        p = match(db.Player, username=username).one()
        if verify(p, password):
            return p
    except NoResultFound:
        pass  # None returned.

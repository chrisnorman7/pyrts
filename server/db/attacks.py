"""Provides the AttackType class."""

from .base import Base, NameMixin, SoundMixin, StrengthMixin


class AttackType(Base, NameMixin, SoundMixin, StrengthMixin):
    """The attack style of a unit."""

    __tablename__ = 'attack_types'

    @property
    def sound(self):
        return f'attack/{self.name}.wav'

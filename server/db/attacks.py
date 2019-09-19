"""Provides the AttackType class."""

from .base import Base, NameMixin, SoundMixin, StrengthMixin


class AttackType(Base, NameMixin, SoundMixin, StrengthMixin):
    """The attack style of a mobile."""

    __tablename__ = 'attack_types'

    @property
    def sound(self):
        return f'static/sounds/attack/{self.name}.wav'

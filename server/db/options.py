"""Provides the Option class."""

from sqlalchemy import Column, String
from yaml import dump, load, FullLoader

from .base import Base, NameMixin

from .. import options


class Option(Base, NameMixin):
    """A single option."""

    __tablename__ = 'options'
    data = Column(String(5000), nullable=False)

    @property
    def value(self):
        return load(self.data, Loader=FullLoader)

    @value.setter
    def value(self, value):
        self.data = dump(value)


options.Option = Option

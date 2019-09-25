"""Provides the Option class."""

from attr import attrs, attrib
from sqlalchemy import Column, String
from yaml import dump, load, FullLoader

from .base import Base, NameMixin

from .. import options


@attrs
class ObjectValue:
    """A dumped object."""

    class_name = attrib()
    id = attrib()

    @property
    def object(self):
        return Base._decl_class_registry[self.class_name].get(self.id)


class Option(Base, NameMixin):
    """A single option."""

    __tablename__ = 'options'
    data = Column(String(5000), nullable=False)

    @property
    def value(self):
        value = load(self.data, Loader=FullLoader)
        if isinstance(value, ObjectValue):
            return value.object
        return value

    @value.setter
    def value(self, value):
        cls = type(value)
        if Base in cls.__bases__:
            # We have a database object. Make an ObjectValue instance.
            value = ObjectValue(cls.__name__, value.id)
        self.data = dump(value)


options.Option = Option

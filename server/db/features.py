"""Provides the Feature class."""

from .base import (
    Base, CoordinatesMixin, NameMixin, LocationMixin, ResourcesMixin,
    TypeMixin, SoundMixin
)

from ..util import english_list


class FeatureType(Base, NameMixin, ResourcesMixin, SoundMixin):
    """A feature type."""

    __tablename__ = 'feature_types'

    @property
    def resources(self):
        """Return a list of names representing the resources this feature type
        provides."""
        names = []
        for name in type(self).resource_names():
            if getattr(self, name) is not None:
                names.append(name)
        return names


class Feature(
    Base, CoordinatesMixin, LocationMixin, ResourcesMixin, TypeMixin
):
    """A fixture or feature on a map."""

    __tablename__ = 'features'
    __type_class__ = FeatureType

    def get_full_name(self):
        resources = []
        for name in self.type.resources:
            value = getattr(self, name)
            resources.append(f'{value} {name}')
        return f'{self.type.name} [{english_list(resources)}]'

    def get_name(self):
        return self.type.name
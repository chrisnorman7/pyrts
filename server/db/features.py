"""Provides the Feature class."""

from .base import (
    Base, CoordinatesMixin, NameMixin, LocationMixin, ResourcesMixin,
    TypeMixin, SoundMixin, GetNameMixin
)


class FeatureType(Base, NameMixin, ResourcesMixin, SoundMixin):
    """A feature type. Resources are used to decide which resources features of
    this type provide."""

    __tablename__ = 'feature_types'


class Feature(
    Base, CoordinatesMixin, LocationMixin, ResourcesMixin, TypeMixin,
    GetNameMixin
):
    """A fixture or feature on a map. Resources are used for storage."""

    __tablename__ = 'features'
    __type_class__ = FeatureType

    def get_full_name(self):
        """Get this feature's name with all the stored resources."""
        return f'{self.get_name()} [{self.resources_string()}]'

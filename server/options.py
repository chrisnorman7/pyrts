"""Provides the Options class, and options instance."""

import os.path

from socket import getfqdn

from sqlalchemy.orm.exc import NoResultFound

from .exc import NoSuchOption, DuplicateOption

Option = None


class Options:
    """Reads and writes option rows from the database."""

    def __init__(self):
        """Add a defaults dictionary."""
        self.defaults = {}

    def __dir__(self):
        return [x.name for x in Option.all()]

    def __repr__(self):
        string = f'{type(self).__name__}('
        args = []
        for name in dir(self):
            args.append(f'{name}={repr(getattr(self, name))}')
        string += ', '.join(args)
        string += ')'
        return string

    def __getattr__(self, name):
        """Get an option from the database."""
        if Option is None:
            return super().__getattribute__(name)
        try:
            return self.get_option(name).value
        except NoSuchOption:
            if name in self.defaults:
                return self.defaults[name]
            return super().__getattribute__(name)

    def has_option(self, name):
        """Return True if we have an option by the given name, False
        otherwise."""
        return bool(Option.count(name=name)) or name in self.defaults

    def get_option(self, name):
        """Get an option row with the given name."""
        try:
            return Option.one(name=name)
        except NoResultFound:
            raise NoSuchOption(name)

    def __setattr__(self, name, value):
        """Set an option's value."""
        if Option is None:
            return super().__setattr__(name, value)
        try:
            o = self.get_option(name)
        except NoSuchOption:
            if name in self.defaults:
                o = self.add_option(name, value)
            else:
                return super().__setattr__(name, value)
        o.value = value
        o.save()

    def set_default(self, name, value):
        """Add a name / value pair to the self.defaults dictionary."""
        self.defaults[name] = value

    def add_option(self, name, value):
        """Create a new option."""
        if Option.count(name=name):
            raise DuplicateOption(name)
        o = Option(name=name)
        o.value = value
        o.save()
        return o

    def remove_option(self, name):
        """Delete the named option."""
        return Option.query(name=name).delete()

    def set_defaults(self):
        """Set some defaults."""
        self.set_default('interface', '0.0.0.0')
        self.set_default('http_port', 7873)
        self.set_default('websocket_port', self.http_port + 1)
        self.set_default('server_name', 'RTS')
        self.set_default('base_url', f'http://{getfqdn()}:{self.http_port}/')
        self.set_default('static_path', 'static')
        self.set_default(
            'sounds_path', os.path.join(self.static_path, 'sounds')
        )
        self.set_default(
            'sounds_url',
            f'{self.base_url}{self.sounds_path.replace(os.path.sep, "/")}/'
        )
        self.set_default('start_music', f'{self.sounds_url}music/start.wav')
        self.set_default('volume_adjust', 0.01)
        self.set_default('start_building', None)


options = Options()

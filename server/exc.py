"""Provides exception classes."""


class Error(Exception):
    pass


class AuthenticationError(Error):
    """Authentication problem."""


class InvalidUsername(AuthenticationError):
    """No player with that username found."""


class InvalidPassword(AuthenticationError):
    """Invalid password for that player."""


class CommandError(Error):
    """An error with the commands system."""


class InvalidArgument(CommandError):
    """An invalid argument was passed."""


class SoundError(Error):
    """There was an error in the sounds framework."""


class NoSuchSound(SoundError):
    """There is no such sound."""

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


class DBError(Error):
    """A database error."""


class InvalidName(DBError):
    """An invalid name was passed."""


class OptionsError(Error):
    """Error with the options framework."""


class NoSuchOption(OptionsError):
    """There is no option with that name."""


class DuplicateOption(OptionsError):
    """Tried to create a duplicate option."""


class EventException(Error):
    """An event error."""


class DuplicateName(EventException):
    """There is already an event with that name."""


class NoSuchEvent(EventException):
    """There is no event with that name."""


class NoSuchListener(EventException):
    """That listener does not exist."""

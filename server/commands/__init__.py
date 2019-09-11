"""The commands system."""

from .commands import command

# Modules containing commands.
from . import administration, communication, general, maps, movement

__all__ = [
    'administration', 'command', 'communication', 'general', 'maps', 'movement'
]

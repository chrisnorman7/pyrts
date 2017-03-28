"""The server code."""

import re
from datetime import datetime
from attr import attrs, attrib
from twisted.python import log
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, protocol
from util import notify_player
from db import Player
from commands.base import commands, anonymous_commands, games_menu
from config import welcome_msg


@attrs
class FakePlayer:
    """A pretend player class."""
    connection = attrib()

    def __attrs_post_init__(self):
        self.connected = True

    def notify(self, *args, **kwargs):
        return notify_player(self, *args, **kwargs)

    def disconnect(self):
        """Disconnect this player."""
        self.connection.transport.loseConnection()


class Protocol(LineReceiver):
    """The protocol for dealing with clients."""
    def connectionMade(self):
        self.last_command = None
        self.connected = datetime.now()
        self.game = None
        self.player = FakePlayer(self)
        self.player.notify(welcome_msg)

    def connectionLost(self, reason):
        """Destroy all the players stuff."""
        log.msg(
            '%r disconnected: %s.' % (
                self.player,
                reason.getErrorMessage()
            )
        )
        self.player.connection = None

    def get_commands(self):
        """Returns the possible commands for this connection."""
        if isinstance(self.player, FakePlayer):
            return anonymous_commands
        elif isinstance(self.player, Player):
            if self.player.game is None:
                return games_menu
            else:
                return commands
        else:
            return []  # No idea what's going on.

    def lineReceived(self, string):
        string = string.decode()
        if string == '!':
            if self.last_command is not None:
                string = self.last_command
            else:
                return self.player.notify('This is your first command.')
        else:
            self.last_command = string
        for command in self.get_commands():
            m = re.match(command.regexp, string)
            if m is not None:
                log.msg('Running %r with match %r.' % (command, m))
                command.func(self.player, m)
                break
        else:
            self.player.notify('Unrecognised.')


class Factory(protocol.ServerFactory):
    """Server factory."""
    protocol = Protocol


def start(host, port):
    """Start the server listening."""
    reactor.listenTCP(port, Factory(), interface=host)
    reactor.run()

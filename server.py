"""The server code."""

import re
from datetime import datetime
from random import random
from math import floor
from twisted.python import log
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, protocol
from db import Player, Game, GameObject, session
from buildings import town_hall
from util import object_created
from commands.base import commands


class Protocol(LineReceiver):
    """The protocol for dealing with clients."""
    def connectionMade(self):
        self.last_command = None
        self.connected = datetime.now()
        game = session.query(Game).first()
        if game is None:
            game = Game()
            game.save()
            log.msg('Created new game %r.' % game)
        self.player = Player(
            game=game,
            name='Player',
            start_x=float(floor(random() * game.size_x)),
            start_y=float(floor(random() * game.size_y)),
        )
        self.player.connection = self
        self.player.save()
        self.player.name = 'Player %d' % self.player.id
        for obj in session.query(
            Player
        ).filter(
            Player.game == game,
            Player.id != self.player.id
        ):
            obj.notify('{} connected.', self.player.name)
        self.player.save()
        log.msg('Created player %r.' % self.player)
        # Give the player their first building:
        building = GameObject(
            game=game,
            owner=self.player,
            x=self.player.start_x,
            y=self.player.start_y
        )
        log.msg('Created building %r.' % building)
        building.target_x = building.x
        building.target_y = building.y
        building.type = town_hall
        self.player.notify(
            'The board is {} by {}.',
            game.size_x,
            game.size_y
        )
        self.player.notify(
            'Your location: ({}, {}).',
            self.player.start_x,
            self.player.start_y
        )
        object_created(building)

    def connectionLost(self, reason):
        """Destroy all the players stuff."""
        log.msg(
            '%r disconnected: %s.' % (
                self.player,
                reason.getErrorMessage()
            )
        )
        game = self.player.game
        for obj in session.query(
            Player
        ).filter(
            Player.game == self.player.game,
            Player.id != self.player.id
        ):
            obj.notify('{} disconnected.', self.player.name)
        for obj in [self.player, *self.player.owned_objects]:
            log.msg('Deleting object %r.' % obj)
            session.delete(obj)
        session.commit()
        if not game.objects and not game.players:
            log.msg('Deleting game %r.' % game)
            session.delete(game)
            session.commit()

    def lineReceived(self, string):
        string = string.decode()
        if string == '!':
            if self.last_command is not None:
                string = self.last_command
            else:
                return self.player.notify('This is your first command.')
        else:
            self.last_command = string
        for command in commands:
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

"""Provides the web server."""

import os.path

from json import dumps, loads
from logging import getLogger
from socket import getfqdn

from autobahn.twisted.websocket import WebSocketServerProtocol
from klein import Klein
from twisted.web.static import File

from .commands.commands import commands, LocationTypes
from .db import Map, Feature, Player
from .options import websocket_port, start_music

app = Klein()


@app.route('/')
def index(request):
    """Return the index page."""
    with open(os.path.join('templates', 'index.html'), 'r') as f:
        return f.read()


@app.route('/static/', branch=True)
def static(request):
    """Return the static directory."""
    return File('static')


@app.route('/stats')
def db_stats(request):
    """Return a dictionary of database statistics."""
    d = dict(maps=Map.count(), features=Feature.count())
    return dumps(d).encode()


@app.route('/constants.js', branch=False)
def js_constants(request):
    socket_url = f'ws://{getfqdn()}:{websocket_port}'
    s = f'const socketUrl = "{socket_url}"\n\nconst hotkeys = {{'
    hotkeys = [
        f'"{cmd.hotkey}": "{name}"' for name, cmd in commands.items()
        if cmd.hotkey
    ]
    if hotkeys:
        s += '\n    '
    s += ',\n    '.join(hotkeys)
    s += '\n}\n'
    return s


class WebSocketProtocol(WebSocketServerProtocol):
    """For communication between the game and the browser."""

    def connectionMade(self):
        """Create a logger."""
        super().connectionMade()
        self.player_id = None
        peer = self.transport.getPeer()
        self.logger = getLogger('%s:%d' % (peer.host, peer.port))
        self.logger.info('Connected.')

    def connectionLost(self, reason):
        super().connectionLost(reason)
        self.logger.info(reason.getErrorMessage())
        if self.player is not None:
            self.player.connected = False
            self.player.connection = None

    def onOpen(self):
        """Send a welcome message."""
        self.message('Welcome. Please login or create a character.')
        self.send('start_music', start_music)

    def send(self, command, *args):
        """Send a command to this websocket."""
        data = dict(command=command, args=args)
        self.sendMessage(dumps(data).encode())

    def sound(self, url):
        """Play a single sound without looping."""
        self.send('sound', url)

    def message(self, string):
        """Send a message to this socket."""
        self.send('message', string)

    def stop_loops(self):
        """Tell the client to stop all playing loops."""
        self.send('stop_loops')

    def start_loop(self, url):
        """Tell the client to start looping the given path."""
        self.send('start_loop', url)

    def menu(self, menu):
        """Send a menu to this connection."""
        self.send('menu', menu.dump())

    def onMessage(self, payload, binary):
        """A message was received."""
        if binary:
            raise RuntimeError('Binary payloads not supported.')
        data = loads(payload.decode())
        name = data['command']
        kwargs = data['args']
        self.call_command(name, **kwargs)

    def call_command(self, _name, **kwargs):
        """Call a command on this connection."""
        if _name not in commands:
            self.message('No such command: %r.' % _name)
            return False
        command = commands[_name]
        player = self.player
        if player is None and command.login_required:
            self.message('You must be logged in to use this command.')
            return False
        elif command.admin and not player.admin:
            self.message('Only administrators can use this command.')
            return False
        if player is None:
            location = None
            entry_point = None
        else:
            location = player.location
            entry_point = player.entry_point
        lt = command.location_type
        if lt is not LocationTypes.any:
            not_map = 'You are not on a map.'
            if lt is LocationTypes.not_map and location is not None:
                self.message('You cannot use this command while on a map.')
                return False
            elif lt is LocationTypes.map and location is None:
                self.message(not_map)
                return False
            elif lt is LocationTypes.not_template:
                if location is None:
                    self.message(not_map)
                    return False
                elif location.template:
                    self.message(
                        'You cannot use this command while editing a template.'
                    )
                    return False
            elif lt is LocationTypes.template:
                if location is None:
                    self.message(not_map)
                    return False
                elif not location.template:
                    self.message(
                        'You can only use this command while editing a '
                        'template.'
                    )
                    return False
            elif lt is LocationTypes.not_finalised:
                if location is None:
                    self.message(not_map)
                    return False
                elif location.finalised is not None:
                    self.message(
                        'You cannot use this command during a running game.'
                    )
                    return False
            elif lt is LocationTypes.finalised:
                if location is None:
                    self.message(not_map)
                    return False
                elif location.finalised is None:
                    self.message(
                        'You cannot use this command until the game has begun.'
                    )
                    return False
        try:
            command.call(
                con=self, command_name=_name, player=player, location=location,
                entry_point=entry_point, args=kwargs, **kwargs
            )
            return True
        except Exception:
            self.logger.exception(
                'A problem occurred while running command %r.', command
            )
            self.message('There was an error.')

    @property
    def player(self):
        if self.player_id is not None:
            return Player.get(self.player_id)

    def text(
        self, label, command, argument_name='text', value='', args=None
    ):
        """Ask for some text from the user."""
        if args is None:
            args = {}
        self.send('text', label, command, argument_name, value, args)

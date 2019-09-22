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
from .options import options
from .util import format_exception

hostname = getfqdn()
app = Klein()


@app.route('/')
def index(request):
    """Return the index page."""
    h = f'{hostname.lower()}:{options.http_port}'.encode()
    if request.requestHeaders.getRawHeaders(b'host', [None])[0] != h:
        return request.redirect(f'http://{hostname}:{options.http_port}')
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
    socket_url = f'ws://{hostname}:{options.websocket_port}'
    return f'const socketUrl = "{socket_url}"\n'


class WebSocketProtocol(WebSocketServerProtocol):
    """For communication between the game and the browser."""

    def connectionMade(self):
        """Create a logger."""
        super().connectionMade()
        self.player_id = None
        self.set_logger()
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
        self.send('start_music', options.start_music)
        hotkeys = {}
        for command in commands.values():
            if command.hotkey is not None:
                hotkeys[command.hotkey] = command.name
        self.send('hotkeys', hotkeys)

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

    def get_default_kwargs(self, player=None, location=None, entry_point=None):
        """Get the default keyword arguments that are sent to every command."""
        if player is None:
            player = self.player
        if location is None and player is not None:
            location = player.location
        if entry_point is None and player is not None:
            entry_point = player.entry_point
        return dict(
            con=self, player=player, location=location, entry_point=entry_point
        )

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
        default_kwargs = self.get_default_kwargs(
            player=player, location=location, entry_point=entry_point
        )
        try:
            command.call(
                **default_kwargs, command_name=_name, args=kwargs, **kwargs
            )
            return True
        except Exception as e:
            self.logger.exception(
                'A problem occurred while running command %r.', command
            )
            if player is None or not player.admin:
                self.message('There was an error.')
            else:
                self.message(format_exception(e))

    def set_logger(self, player=None):
        """Set self.logger to a logger with a sensible name."""
        if player is None:
            peer = self.transport.getPeer()
            name = f'{peer.host}:{peer.port}'
        else:
            name = f'{player.name} (#{player.id})'
        self.logger = getLogger(name)

    def authenticated(self, player):
        """This connection has successfully logged in as the given Player
        instance."""
        self.player_id = player.id
        self.message('Welcome, %s.' % player.name)
        player.send_title()
        self.send("authenticated")
        self.set_logger(player=player)
        self.logger.info('Authenticated.')

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

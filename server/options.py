"""Configuration options. Can probably be overridden with command line
arguments."""

import os.path

from socket import getfqdn

interface = '0.0.0.0'
http_port = 7873
websocket_port = http_port + 1

base_url = f'http://{getfqdn()}:{http_port}/'
static_path = 'static'
sounds_path = os.path.join(static_path, 'sounds')
sounds_url = f'{base_url}{sounds_path.replace(os.path.sep, "/")}/'
start_music = f'{sounds_url}music/start.wav'

volume_adjust = 0.01

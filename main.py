"""The main entry point."""

import logging

from autobahn.twisted.websocket import listenWS, WebSocketServerFactory
from twisted.internet import reactor
from twisted.web.server import Site

from server.db import Base, load, dump, Mobile
from server.options import interface, http_port, websocket_port
from server.util import pluralise
from server.web import app, WebSocketProtocol


def main():
    """Run the server."""
    logging.basicConfig(level='INFO')
    logging.info('Starting server...')
    try:
        load()
        logging.info('Number of objects loaded: %d.', Base.number_of_objects())
        q = Mobile.query(Mobile.action.isnot(None),)
        c = q.count()
        if c:
            logging.info('Resuming %d %s.', c, pluralise(c, 'task'))
            for m in q:
                m.start_task()
        else:
            logging.info('No tasks to resume.')
    except FileNotFoundError:
        logging.info('Starting with a blank database.')
    site = Site(app.resource())
    port = reactor.listenTCP(http_port, site, interface=interface)
    logging.info(
        'Listening for HTTP connections on %s:%d.', port.interface, port.port
    )
    factory = WebSocketServerFactory(
        'ws://%s:%d' % (interface, websocket_port)
    )
    factory.protocol = WebSocketProtocol
    port = listenWS(factory, interface=interface)
    logging.info(
        'Listening for websockets on %s:%d.', port.interface, port.port
    )
    reactor.run()
    dump()
    logging.info('Objects dumped: %d.', Base.number_of_objects())


if __name__ == '__main__':
    main()

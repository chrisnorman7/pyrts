"""The main entry point."""

import logging

from time import time

from autobahn.twisted.websocket import listenWS, WebSocketServerFactory
from twisted.internet import reactor
from twisted.web.server import Site

from server.db import Base, load, dump, setup, Unit, Transport
from server.options import options
from server.tasks import task
from server.util import pluralise
from server.web import app, WebSocketProtocol

dump_logger = logging.getLogger('Database Dump')


def dump_task():
    """Dump the database every half an hour."""
    started = time()
    dump_logger.info('Starting dump...')
    dump('world.dump')
    dump_logger.info('Dump completed in %.2f seconds.', time() - started)


def main():
    """Run the server."""
    loading_started = time()
    logging.basicConfig(level='INFO')
    logging.info('Starting server...')
    logging.info('Phase: Load database.')
    try:
        started = time()
        load()
        logging.info(
            'Number of objects loaded: %d (%.2f seconds).',
            Base.number_of_objects(), time() - started
        )
        logging.info('Phase: Start tasks.')
        q = Unit.query(Unit.action.isnot(None),)
        c = q.count()
        if c:
            logging.info('Resuming %d %s.', c, pluralise(c, 'task'))
            for m in q:
                m.start_task()
        else:
            logging.info('No tasks to resume.')
        logging.info('Phase: Check for airborn transports.')
        for t in Transport.all(Transport.land_time < time()):
            logging.info('Landing %s.', t.unit.get_name())
            Transport.land(t.id)
    except FileNotFoundError:
        logging.info('Starting with a blank database.')
    logging.info('Phase: Database setup.')
    setup()
    logging.info('Phase: Add dump schedule.')
    task(3600, now=False)(dump_task)
    logging.info('Phase: Setup listeners.')
    site = Site(app.resource())
    port = reactor.listenTCP(
        options.http_port, site, interface=options.interface
    )
    logging.info(
        'Listening for HTTP connections on %s:%d.', port.interface, port.port
    )
    factory = WebSocketServerFactory(
        'ws://%s:%d' % (options.interface, options.websocket_port)
    )
    factory.protocol = WebSocketProtocol
    port = listenWS(factory, interface=options.interface)
    logging.info(
        'Listening for websockets on %s:%d.', port.interface, port.port
    )
    logging.info(
        'Initialisation completed in %.2f seconds.', time() - loading_started
    )
    logging.info('Phase: Main loop.')
    reactor.run()
    logging.info('Phase: Dump database.')
    started = time()
    dump()
    logging.info(
        'Objects dumped: %d (%.2f seconds).', Base.number_of_objects(),
        time() - started
    )


if __name__ == '__main__':
    main()

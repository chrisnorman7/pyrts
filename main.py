"""Main entry point."""

from sys import stdout
from argparse import ArgumentParser, FileType
from twisted.python import log
from server import start

parser = ArgumentParser()
parser.add_argument(
    'log_file', type=FileType('w'),
    nargs='?',
    default=stdout,
    help='The file to write log output to'
)

if __name__ == '__main__':
    args = parser.parse_args()
    log.startLogging(args.log_file)
    start('0.0.0.0', 7873)

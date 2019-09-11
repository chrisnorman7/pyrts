"""Update index.html with random get params."""

import os.path
import re

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
from time import time

# This regexp is used so that the static file editor can bump version numbers
# in the given file.
src_regexp = 'src="([^?]+)[?]([0-9]+)["]'

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

parser.add_argument(
    'filename', nargs='?', default=os.path.join('templates', 'index.html'),
    type=FileType('r'), help='The file to modify.'
)


def file_updated(f):
    """A file has been updated."""
    path = f.name
    now = int(time())

    def repl(m):
        """Used with re.sub."""
        filename, i = m.groups()
        i = int(i)
        print('Bumping %s: %d -> %d.' % (filename, i, now))
        return 'src="%s?%d"' % (filename, now)

    code = f.read()  # Get the code.
    f.close()
    if not re.findall(src_regexp, code):
        raise RuntimeError(
            'No linkd files found in %s.' % path
        )
    # Alter the code in memory.
    code = re.sub(src_regexp, repl, code)
    # Now write the file back to index.html.
    with open(path, 'w') as f:
        f.write(code)


if __name__ == '__main__':
    args = parser.parse_args()
    try:
        file_updated(args.filename)
        print('Done.')
    except RuntimeError as e:
        print(*e.args)

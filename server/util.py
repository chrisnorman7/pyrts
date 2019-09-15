"""Utility functions."""

from traceback import format_exception as _format_exception


def pluralise(n, singular, plural=None):
    """Return singular or plural, depending on the value of n. If plural is
    None, it will be set to singular with a letter s tacked onto the end."""
    if plural is None:
        plural = singular + 's'
    if n == 1:
        return singular
    return plural


def is_are(n):
    """Return "is" or "are" depending on the value of n."""
    if n == 1:
        return 'is'
    else:
        return 'are'


def english_list(l, empty='nothing', key=str, sep=', ', and_='and '):
    """Return a decently-formatted list."""
    results = [key(x) for x in l]
    if not results:
        return empty
    if len(results) == 1:
        return results[0]
    res = ''
    for pos, item in enumerate(results):
        if pos == len(results) - 1:
            res += f'{sep}{and_}'
        elif res:
            res += sep
        res += item
    return res


def difference_string(d, empty='nothing'):
    """Given the result of ResourcesMixin.get_difference as a dictionary d,
    return a sensible string."""
    strings = [f'{value} {name}' for name, value in d.items()]
    return english_list(strings, empty=empty)


def format_exception(e):
    """Return a string representing the provided Exception instance."""
    return ''.join(_format_exception(type(e), e, e.__traceback__))

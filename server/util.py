"""Utility functions."""


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

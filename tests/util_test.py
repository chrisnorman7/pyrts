from server.util import is_are


def test_is_are():
    assert is_are(0) == 'are'
    assert is_are(1) == 'is'
    assert is_are(1234) == 'are'

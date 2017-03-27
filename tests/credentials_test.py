"""Test credentials."""

from credentials import create_player, verify, authenticate


password = 'I am a Password'


def test_create_player():
    uid = 'test username'
    p = create_player(uid, password)
    assert p.username == uid
    assert verify(p, password) is True


def test_authenticate():
    p = create_player('another test user', password)
    assert authenticate(p.username, password) is p
    assert authenticate('not really a user', password) is None
    assert authenticate(p.username, 'wrong password') is None

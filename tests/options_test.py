from pytest import raises

from server.db import Option
from server.options import options


def test_add_option():
    o = options.add_option('name', 'value')
    assert isinstance(o, Option)
    assert o.name == 'name'
    assert o.value == 'value'


def test_get():
    options.add_option('port', 1234)
    assert options.port == 1234
    with raises(AttributeError) as exc:
        options.fails
    assert exc.value.args == ('fails',)


def test_set():
    options.add_option('set', 'hello world')
    options.set = '1236'
    assert options.set == '1236'


def test_option():
    o = Option(name='hello', data='world')
    assert o.value == 'world'
    o.value = 'something'
    assert o.value == 'something'
    o.value = True
    assert o.value is True
    o.value = 1234
    assert o.value == 1234


def remove_option():
    options.add_option('works', 'value')
    assert options.works == 'value'
    options.remove_option('works')
    with raises(AttributeError):
        options.works

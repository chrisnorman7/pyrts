from pytest import raises

from server.db import Option
from server.options import options


def test_add_option():
    o = options.add_option('name', 'value')
    assert isinstance(o, Option)
    assert o.name == 'name'
    assert o.value == 'value'
    assert o.id is not None


def test_get():
    options.add_option('port', 1234)
    assert options.port == 1234
    with raises(AttributeError):
        options.fails


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


def test_remove_option():
    options.add_option('works', 'value')
    assert options.works == 'value'
    options.remove_option('works')
    with raises(AttributeError):
        options.works


def test_object_option(mine):
    o = options.add_option('mine', mine)
    assert o.value is mine


def test_has_option():
    assert not options.has_option('not even there')
    options.set_default('test', 'value')
    assert options.has_option('test')


def test_getattr():
    with raises(AttributeError):
        options.hopefully_no_options_with_this_name


def test_setattr():
    options.test_setattr = 5
    assert options.__dict__['test_setattr'] == 5


def test_get_default():
    options.set_default('asdfghjkl', 1024)
    assert options.defaults['asdfghjkl'] == 1024
    assert options.asdfghjkl == 1024
    assert not Option.count(name='asdfghjkl')

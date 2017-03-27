"""Test the database."""

from db import Game, Player, GameObject
from objects import TYPE_FEATURE, TYPE_MOBILE, TYPE_BUILDING
from features import feature_types
from mobiles import mobile_types
from buildings import building_types

player_name = 'test the db player'
game = Game()
game.save()
player = Player(name=player_name, username=player_name, game=game)
player.save()


def test_game():
    assert game.objects == []
    assert game.players == [player]


def test_Player():
    assert player.game is game
    assert player.name == player_name
    assert player.owned_objects == []
    assert player.gold == 50
    assert player.food == 50


def test_feature():
    parent = list(feature_types.values())[0]
    assert parent.type_flag is TYPE_FEATURE
    f = GameObject(
        game=game,
        owner=player,
        type_flag=TYPE_FEATURE,
        type_parent=parent.name
    )
    f.save()
    assert f.type is parent


def test_mobile():
    parent = list(mobile_types.values())[0]
    assert parent.type_flag is TYPE_MOBILE
    m = GameObject(
        game=game,
        owner=player,
        type_flag=TYPE_MOBILE,
        type_parent=parent.name
    )
    assert m.type is parent


def test_building():
    parent = list(building_types.values())[0]
    assert parent.type_flag is TYPE_BUILDING
    b = GameObject(
        game=game,
        owner=player,
        type_flag=TYPE_BUILDING,
        type_parent=parent.name
    )
    assert b.type is parent


def test_change_type():
    feature = feature_types['Empty Land']
    building = building_types['Town Hall']
    o = GameObject(
        game=game,
        owner=player,
        type_flag=feature.type_flag,
        type_parent=feature.name
    )
    assert o.type is feature
    o.type = building
    assert o.type is building

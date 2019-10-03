from datetime import datetime, timedelta

from pytest import raises

from server.db import Building, SkillTypes, Skill, SkillType


def test_skill_type(farm):
    st = SkillType(building_type=farm, skill_type=SkillTypes.double_exploit)
    st.save()
    assert st.building_type is farm
    assert st in farm.skill_types
    assert st.skill_type is SkillTypes.double_exploit


def test_add_skill(farm, map):
    b = map.add_building(farm, 0, 0)
    with raises(AssertionError):
        b.add_skill('Must be a member of SkillTypes.')
    assert not b.skills
    s = b.add_skill(SkillTypes.double_exploit)
    assert isinstance(s, Skill)
    assert isinstance(s.activated_at, datetime)
    assert s.id is None  # Not automatically saved.
    s.save()
    assert s.building is b
    assert s in b.skills


def test_delete_skilled_building(map, farm):
    b = map.add_building(farm, 0, 0)
    b.save()
    s = b.add_skill(SkillTypes.double_exploit)
    s.save()
    Building.delete_all(id=b.id)
    assert Building.get(b.id) is None
    assert Skill.get(s.id) is None


def test_skill_types(farm, map):
    b = map.add_building(farm, 0, 0)
    b.save()
    assert not b.skills
    s = b.add_skill(SkillTypes.random_resurrect)
    s.save()
    assert s.skill_type in b.skill_types


def test_building_has_skill(farm, map):
    b = map.add_building(farm, 0, 0)
    b.save()
    v = SkillTypes.double_exploit
    assert not b.has_skill(v)
    b.add_skill(v).save()
    assert b.has_skill(v)


def test_player_has_skill(farm, player, map):
    player.location = map
    b = map.add_building(farm, 0, 0)
    b.owner = player
    assert player.owned_buildings == [b]
    assert not b.skills
    player.save()
    v = SkillTypes.double_exploit
    assert not player.has_skill(v)
    when = datetime.utcnow() + timedelta(seconds=10)
    s = b.add_skill(v, activate=when)
    s.save()
    assert not player.has_skill(v)
    s.activated_at = datetime.utcnow()
    s.save()
    assert player.has_skill(v) == 1
    b2 = map.add_building(farm, 1, 1)
    b2.owner = player
    assert player.has_skill(v) == 1
    b2.add_skill(v).save()
    player.has_skill(v) == 2

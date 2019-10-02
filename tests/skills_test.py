from server.db import SkillTypes, Skill, SkillType


def test_skill_type(farm):
    st = SkillType(building_type=farm, skill_type=SkillTypes.double_exploit)
    st.save()
    assert st.building_type is farm
    assert st in farm.skill_types
    assert st.skill_type is SkillTypes.double_exploit


def test_skill(farm, map):
    b = map.add_building(farm, 0, 0)
    b.save()
    assert not b.skills
    s = Skill(building=b, skill_type=SkillTypes.random_resurrect)
    s.save()
    assert s in b.skills
    assert s.skill_type in b.skill_types

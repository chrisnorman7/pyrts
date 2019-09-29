from server.db import load, Unit, Building, setup, dump

load()
setup()
for cls in (Building, Unit):
    for obj in cls.all(cls.owner_id.isnot(None)):
        obj.set_owner(obj.owner)
        obj.save()
dump()

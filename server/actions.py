"""Provides the various action classes that are used by Unit.progress."""

from random import randint

from attr import attrs, attrib, Factory

from .db import Building
from .events import (
    fire, on_attack, on_drop, on_exhaust, on_exploit, on_heal, on_repair
)

NoneType = type(None)


@attrs
class BaseAction:
    """The base for all other actions. Simply holds a reference to the unit
    that initiated a given action."""

    unit = attrib()

    def enact(self):
        raise NotImplementedError


@attrs
class CombatAction(BaseAction):
    """An action in combat."""

    amount = attrib(default=Factory(int), init=False)

    def enact(self):
        """Carry out this action."""
        unit = self.unit
        t = unit.type
        damage = max(1, t.strength + t.attack_type.strength - t.resistance)
        self.damage = randint(1, damage)
        fire(on_attack)
        player = unit.owner
        target = self.target
        adversary = target.owner
        if isinstance(target, Building):
            unit.sound('destroy.wav')
        else:
            unit.sound(unit.type.attack_type.sound)
            target.sound('ouch.wav')
            if target.action is None:
                target.attack(unit)
        target.hp -= self.amount
        if target.hp < 0:
            if isinstance(target, Building):
                target.sound('collapse.wav')
                unit.sound('destroyed.wav')
                word = 'destroyed'
            else:
                target.sound('die.wav')
                word = 'killed'
            if adversary is not None:
                adversary.message(f'{target.get_name()} has been {word}.')
            for name in target.resources:
                value = getattr(target, name)
                setattr(unit, name, getattr(unit, name) + value)
            target.delete()
            if adversary is not None:
                if adversary.has_lost():
                    for p in unit.location.players:
                        if p is player:
                            p.sound('beat.wav')
                            p.message(f'You beat {adversary.get_name()}.')
                        elif p is adversary:
                            p.sound('lose.wav')
                            p.message(
                                f'You are beaten by {player.get_name()}.'
                            )
                            p.leave_map()
                            p.losses += 1
                            p.save()
                        else:
                            p.message(
                                f'{player.name()} beats '
                                f'{adversary.get_name()}.'
                            )
                    if player.has_won():
                        player.message('You have won!')
                        player.sound('win.wav')
                        player.wins += 1
                        player.save()


@attrs
class ExploitAction(BaseAction):
    """The action used when exploiting buildings or features."""

    amount = attrib(default=Factory(NoneType))
    resource_name = attrib(default=Factory(NoneType))

    def enact(self):
        """Take the resources."""
        unit = self.unit
        t = unit.type
        self.resource_name = unit.exploiting_material
        self.amount = getattr(t, self.resource_name)
        fire(on_exploit, self)
        target = unit.exploiting
        name = self.resource_name
        amount = self.amount
        value = getattr(target, name)
        if not value:
            # Empty resource.
            unit.speak('finished')
            return unit.reset_action()
        unit.sound(f'exploit/{name}.wav')
        amount = min(amount, value)
        setattr(unit, name, amount)
        value -= amount
        setattr(target, name, value)
        target.save()
        if not value:
            fire(on_exhaust, unit, target, name)
        unit.action = unit.UnitActions.drop


@attrs
class DropAction(BaseAction):
    """Drop off resources at self.unit.home."""

    def enact(self):
        """Drop the goods."""
        fire(on_drop, self)
        unit = self.unit
        for name in unit.resources:
            value = getattr(unit, name)
            setattr(unit, name, 0)
            setattr(unit.home, name, getattr(unit.home, name) + value)
        unit.sound('drop.wav')
        unit.action = unit.UnitActions.exploit


@attrs
class HealRepairAction(BaseAction):
    """Used when healing other units or repairing buildings. When coding for
    units, use HealAction and RepairAction instead."""

    target = attrib(default=Factory(NoneType), init=False)
    amount = attrib(default=Factory(int), init=False)
    sound = attrib(default=Factory(NoneType), init=False)

    def get_particulars(self):
        raise NotImplementedError

    def enact(self):
        """Perform the healing."""
        amount, self.sound, event_name = self.get_particulars()
        self.amount = randint(1, amount)
        fire(event_name, self)
        unit = self.unit
        amount = self.amount
        sound = self.sound
        target = self.target
        if target is None:
            target = unit.exploiting
        target.heal(amount)
        target.save()
        unit.sound(sound)
        if target.health is None:
            unit.speak('finished')
            unit.reset_action()


class HealAction(HealRepairAction):
    """Used hwen heading other units."""

    def get_particulars(self):
        return (self.unit.type.heal_amount, 'heal.wav', on_heal)


@attrs
class RepairAction(HealRepairAction):
    """Used when repairing buildings."""

    def get_particulars(self):
        return (self.unit.type.repair_amount, 'repair.wav', on_repair)

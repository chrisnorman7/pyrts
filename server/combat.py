"""Provides the CombatAction class."""

from attr import attrs, attrib

from .db import Building


@attrs
class CombatAction:
    """An action in combat."""

    attacker = attrib()
    target = attrib()
    damage = attrib()

    def enact(self):
        """Carry out this action."""
        unit = self.attacker
        player = unit.owner
        target = self.target
        adversary = target.owner
        if isinstance(target, Building):
            unit.sound('destroy.wav')
        else:
            unit.sound(unit.type.attack_type.sound)
            target.sound('ouch.wav')
            if target.type.action is not None:
                target.attack(unit)
        target.hp -= self.damage
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

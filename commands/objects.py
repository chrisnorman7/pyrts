"""Object-level commands."""


def spawn_mobile(parent, type):
    """Spawn a mobile of type type at the same location as parent."""
    m = parent.__class__(
        game=parent.game,
        x=parent.x,
        y=parent.y,
        target_x=parent.x,
        target_y=parent.y,
        owner=parent.owner
    )
    m.type = type
    for player in m.game.players:
        player.notify(
            '{} steps out of {} at ({}, {}).',
            m.name,
            parent.name,
            m.x,
            m.y
        )


def recruit(player, obj, argument):
    """Recruit a mobile."""
    name = argument.lower().strip()
    for type in obj.type.provides:
        if type.name.lower().startswith(name):
            # We found the right mobile.
            for attr in ['wood', 'gold', 'food', 'water']:
                if getattr(player, attr) < getattr(type, attr):
                    player.notify('Not enough {}.', attr)
                    break
                else:
                    setattr(
                        player,
                        attr,
                        getattr(
                            player,
                            attr
                        ) - getattr(
                            type,
                            attr
                        )
                    )
            else:
                player.notify(
                    '{} recruiting {} ({}).',
                    obj.name,
                    type.name,
                    type.pop_time
                )
                obj.add_action(type.pop_time, spawn_mobile, obj, type)
                break
        else:
            player.notify(
                '{} does not know how to recruit {}.',
                obj.name,
                name
            )

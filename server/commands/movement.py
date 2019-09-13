"""Movement-related commands."""

from .commands import command

from ..db import Building, Feature, Mobile, Player
from ..menus import Menu

directions = {
    'up': (0, 1),
    'right': (1, 0),
    'down': (0, -1),
    'left': (-1, 0),
}


def move_player(player, direction):
    """Move the given player in the given direction."""
    x, y = directions[direction]
    x += player.x
    y += player.y
    loc = player.location
    if loc.valid_coordinates(x, y):
        player.move(x, y)
    else:
        player.message('You cannot move in that direction.')


for direction in directions:
    command(
        hotkey=f'arrow{direction}', name=direction,
        description=f'Move {direction}.'
    )(
        lambda player, command_name: move_player(player, command_name)
    )


@command(hotkey='home')
def home(player, entry_point):
    """Move this player to either their starting point, or 0, 0."""
    if entry_point:
        player.move(entry_point.x, entry_point.y)
    else:
        player.move(0, 0)


@command(hotkey='end')
def end(player, location):
    """Move to the top right corner of the grid."""
    player.move(location.size_x, location.size_y)


@command(hotkey='c')
def coordinates(player, location):
    """Show current coordinates."""
    player.message(f'({player.x}, {player.y})')


@command()
def move(player, location, x, y):
    """Move to a point on the grid."""
    if x < 0 or y < 0 or x > location.size_x or y > location.size_y:
        player.message('You cannot move there.')
    else:
        player.move(x, y)


@command(hotkey='j')
def jump(con, player, location):
    """Move to a feature on the map."""
    objects = []
    for cls in (Player, Building, Mobile, Feature):
        objects.extend(cls.query(location=location))
    objects.remove(player)
    if not objects:
        player.message('This map is empty.')
    else:
        locations = sorted(
            objects, key=lambda thing: player.distance_to(thing)
        )
        m = Menu('Jump')
        for thing in locations:
            m.add_item(
                f'{thing.get_full_name()} ({player.directions_to(thing)})',
                'move',
                args=dict(x=thing.x, y=thing.y)
            )
        m.send(con)


@command(hotkey='g')
def goto(player, location, con, command_name, x=None, y=None):
    """Go to a specific point on the map."""
    if x is None:
        con.text(
            'Enter x coordinate', command_name, argument_name='x',
            value=player.x
        )
    elif y is None:
        con.text(
            'Enter y coordinate', command_name, argument_name='y',
            value=player.y, args={'x': x}
        )
    else:
        try:
            x = int(x)
            y = int(y)
            if location.valid_coordinates(x, y):
                player.move(x, y)
            else:
                player.message('Invalid coordinates.')
        except ValueError:
            player.message('Invalid coordinates.')

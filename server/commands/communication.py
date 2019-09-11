"""Communication commands."""

from .commands import command


@command(hotkey="'")
def speak(player, location, con, command_name, text=None):
    """Say something."""
    if location is None:
        player.message('You cannot speak here.')
    elif not text:
        con.text('Say something', command_name)
    else:
        player.do_social(
            '%1N say%1s: "{text}"', sound='static/sounds/socials/say.wav',
            text=text
        )

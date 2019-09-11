"""Contains the socials factory."""

from emote_utils import PopulatedSocialsFactory

factory = PopulatedSocialsFactory()


@factory.suffix('n', 'name')
def get_name(player, suffix):
    """"you" or "name"."""
    return 'you', player.name

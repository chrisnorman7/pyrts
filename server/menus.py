"""Provides the Menu and MenuItem classes."""

from attr import attrs, attrib, Factory, asdict


@attrs
class MenuLabel:
    """A label in a menu."""

    title = attrib()


@attrs
class MenuItem(MenuLabel):
    """An item in a menu."""

    command = attrib()
    args = attrib(default=Factory(dict))


@attrs
class Menu:
    """A menu holding several labels and / or items."""

    title = attrib()
    dismissable = attrib(default=Factory(lambda: True))
    items = attrib(default=Factory(list), init=False)

    def add_label(self, *args, **kwargs):
        self.items.append(MenuLabel(*args, **kwargs))

    def add_item(self, *args, **kwargs):
        self.items.append(MenuItem(*args, **kwargs))

    def send(self, con):
        """Send this menu to a connection."""
        con.menu(self)

    def dump(self):
        """Return a menu as a dictionary."""
        d = dict(title=self.title, dismissable=self.dismissable)
        items = []
        for item in self.items:
            datum = asdict(item)
            if isinstance(item, MenuItem):
                datum['type'] = 'item'
            elif isinstance(item, MenuLabel):
                datum['type'] = 'label'
            else:
                raise RuntimeError('Invalid menu item: %r.' % item)
            items.append(datum)
        d['items'] = items
        return d


class YesNoMenu(Menu):
    """A menu for asking yes or no questions."""

    def __init__(
        self, title, command, argument_name='response', yes_title='Yes',
        yes_value=True, no_title='No', no_value=False, args=None
    ):
        """Initialise the menu."""
        super().__init__(title)
        if args is None:
            args = {}
        yes_args = args.copy()
        yes_args[argument_name] = yes_value
        self.add_item(yes_title, command, args=yes_args)
        no_args = args.copy()
        no_args[argument_name] = no_value
        self.add_item(no_title, command, args=no_args)

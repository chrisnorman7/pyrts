"""Check for inconsistancies in the database."""

from server.db import load, MobileType


def main():
    load()
    for name in MobileType.resource_names():
        if MobileType.count(getattr(MobileType, name) == 1):
            continue
        else:
            print(f'There is no mobile that can gather {name}.')


if __name__ == '__main__':
    try:
        main()
    except FileNotFoundError:
        print('No database file exists.')

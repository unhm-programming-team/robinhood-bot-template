if __name__ == '__main__':  # only run this test if it is executed directly.

    import sys

    print('\n paths being searched:\n')
    print(sys.path)

    from robinhoodbot import tradingstats

    print('\n trading stats module:', tradingstats)
    print('trading stats dir:', dir(tradingstats))

    from src.robinhoodbot import bot

    print('\n bot module:', bot)   # had to change from misc import * to from .misc import *
    print('bot dir', dir(bot))

    from src.robinhoodbot import *

    print('\n misc module', misc)
    print(dir(misc))

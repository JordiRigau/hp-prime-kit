# __NAME__ - a starter app for the HP Prime.
#
# The file has to be called main.py and its code has to sit at module level:
# that is the entry point, and it runs when the app imports it.
#
# `hpprime.eval` runs a line of PPL and hands the result back. It is the
# bridge, and everything the screen does here goes through it.
#
# One rule that has no forgiveness: only numbers and flat lists of numbers
# may cross that bridge. A list with a string inside closes the app on the
# spot, with no message.

from hpprime import eval as ev, fillrect

WHITE = 0xFFFFFF


def text(y, s):
    # Quotes are stripped: one inside the expression breaks the PPL line.
    s = str(s).replace('"', "'")[:46]
    ev('TEXTOUT_P("%s",G0,3,%d,2,RGB(0,0,0))' % (s, y))


fillrect(0, 0, 0, 320, 240, WHITE, WHITE)
text(10, '__NAME__')
text(40, 'It runs. Press a key.')
ev('WAIT(-1)')

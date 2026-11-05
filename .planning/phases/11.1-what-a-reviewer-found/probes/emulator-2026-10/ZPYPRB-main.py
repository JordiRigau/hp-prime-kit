# ZPYPRB - two open questions about Python on the Prime, on one screen.
#
#     hpprime build ZPYPRB programs/ZPYPRB/main.py
#
# Each line is one hpprime.eval and what it answered, or that it raised.
# Before each step a mark goes into the PPL global PZ: if the app closes,
# type PZ on Home and it names the step that was running.
#
#   micropython.eval-parentheses  TICKS and GETKEY, with and without ()
#   micropython.number-notation   numbers written the way Python writes them
#
# Esc leaves.

from hpprime import eval as ev, fillrect

WHITE = 0xFFFFFF
BLACK = 0x000000
GREEN = 0x008000
RED = 0xC00000
BLUE = 0x1A5FB4

row = [2]


def txt(s, col=BLACK):
    # Quotes are stripped: one inside the expression breaks the PPL line.
    s = str(s).replace('"', "'")[:52]
    ev('TEXTOUT_P("%s",G0,3,%d,1,RGB(%d,%d,%d),314)'
       % (s, row[0], (col >> 16) & 255, (col >> 8) & 255, col & 255))
    row[0] += 14


def mark(t):
    try:
        ev('PZ:="' + t + '"')
    except Exception:
        pass


def kind(r):
    for t, name in ((bool, 'bool'), (int, 'int'), (float, 'float'),
                    (str, 'str'), (list, 'list')):
        if isinstance(r, t):
            return name
    return '?'


def check(expression):
    """One eval: what it answered and its Python type, or that it raised.
    Only the eval is inside the try, so a failure is the eval's."""
    mark('before ' + expression)
    try:
        r = ev(expression)
    except Exception as e:
        txt('%s RAISED %s' % (expression, str(e)[:16]), RED)
        return None
    txt('%s -> %r  %s' % (expression, r, kind(r)), GREEN)
    return r


def number(text, want):
    """A number as text: did it come back as the number it says?"""
    mark('before ' + text)
    try:
        r = ev(text)
    except Exception as e:
        txt('%s RAISED %s' % (text, str(e)[:16]), RED)
        return
    good = isinstance(r, (int, float)) and abs(r - want) <= 1e-9 * abs(want)
    txt('%s -> %r  %s' % (text, r, 'ok' if good else 'WRONG'),
        GREEN if good else RED)


fillrect(0, 0, 0, 320, 240, WHITE, WHITE)
txt('ZPYPRB  Esc leaves', BLUE)

# micropython.eval-parentheses
for e in ('TICKS', 'TICKS()', 'ticks', 'ticks()', 'GETKEY', 'GETKEY()'):
    check(e)

# micropython.number-notation: how Python writes them, and what comes back.
txt('repr(1e20) is %s, repr(1e-20) is %s' % (repr(1e20), repr(1e-20)), BLUE)
number('1e+20', 1e20)
number('1e20', 1e20)
number(repr(float(1e20)), 1e20)
number('1e-20', 1e-20)
number(repr(float(1e-20)), 1e-20)
number('1e+20/1e+19', 10.0)
number('2.5e+300', 2.5e300)

mark('done')
while True:
    try:
        k = ev('GETKEY()')
    except Exception:
        k = -1
    if k == 4:                                # 4 = Esc
        break

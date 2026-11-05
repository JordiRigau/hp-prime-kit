# ZPYNUM - why did every text with "e+" leave ZPYPRB's line blank?
#
#     hpprime build ZPYNUM programs/ZPYNUM/main.py
#
# Question: micropython.number-notation. ZPYPRB printed each text next to
# what eval answered, so a blank line could be the eval or the printing.
# Here they are apart:
#
#   - lines P1 and P2 only PRINT a text starting "1e+20", no eval at all;
#   - lines n1..n4 EVAL a text with "e+" and print only the answer, under a
#     name, with "+" spelled out.
#
# After each eval, PZ holds "nK answered" or "nK raised": if the app
# closes, PZ on Home names the last step. Esc leaves.

from hpprime import eval as ev, fillrect

WHITE = 0xFFFFFF
BLACK = 0x000000
GREEN = 0x008000
RED = 0xC00000
BLUE = 0x1A5FB4

row = [2]


def txt(s, col=BLACK):
    s = str(s).replace('"', "'")[:52]
    ev('TEXTOUT_P("%s",G0,3,%d,1,RGB(%d,%d,%d),314)'
       % (s, row[0], (col >> 16) & 255, (col >> 8) & 255, col & 255))
    row[0] += 14


def mark(t):
    try:
        ev('PZ:="' + t + '"')
    except Exception:
        pass


def plain(s):
    return str(s).replace('+', ' plus ')


def kind(r):
    for t, name in ((bool, 'bool'), (int, 'int'), (float, 'float'),
                    (str, 'str'), (list, 'list')):
        if isinstance(r, t):
            return name
    return '?'


fillrect(0, 0, 0, 320, 240, WHITE, WHITE)
txt('ZPYNUM  Esc leaves', BLUE)

# Printing alone: does a line that starts with 1e+20 show?
txt('P1 1e+20 printed, nothing evaluated')
txt('P2 the same, but not first: x 1e+20')

cases = (('n1', '1e+20', 1e20), ('n2', '2.5e+300', 2.5e300),
         ('n3', '1e+20/1e+19', 10.0), ('n4', '1E+20', 1e20))
for name, text, want in cases:
    txt('%s is %s' % (name, plain(text)), BLUE)
    mark(name + ' before')
    try:
        r = ev(text)
    except Exception as e:
        mark(name + ' raised')
        txt('%s raised: %s' % (name, plain(str(e)[:24])), RED)
        continue
    mark(name + ' answered')
    good = isinstance(r, (int, float)) and abs(r - want) <= 1e-9 * abs(want)
    txt('%s answered %s, a %s: %s' % (name, plain(repr(r)), kind(r),
                                       'right' if good else 'WRONG'),
        GREEN if good else RED)

mark('done')
while True:
    try:
        k = ev('GETKEY()')
    except Exception:
        k = -1
    if k == 4:
        break

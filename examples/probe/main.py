# The probe: the first thing worth putting on a calculator, before writing
# the real app.
#
#     hpprime build PROBE examples/probe/main.py
#     then drag PROBE.hpappdir onto the calculator in the CK window
#
# It is called main.py because it IS the entry point: in every Python app
# examined, the file has that name and its code sits at module level, so it
# runs on import.
#
# In one pass it answers the questions that decide how everything else gets
# written, and that CANNOT be answered from a PC:
#
#   - does the hpprime.eval bridge respond?
#   - does it see the functions in your PPL programs?
#   - what does GETKEY return for each key?
#   - does touch reach Python, and with what coordinates?
#
# WHY IT GOES IN ORDER OF INCREASING RISK
#
# Because a bad call CLOSES THE APP, with no message and no traceback. With
# the dangerous thing last, the point where it dies identifies the cause. And
# every step leaves a mark in a PPL global, which survives the close:
#
#     if the app closes -> go to Home, type  PZ  and press Enter.
#
# That is how the worst trap on this platform was found in a single pass: a
# list with a STRING inside closes the app. Everything crossing the bridge
# has to be a number or a flat list of numbers.

from hpprime import eval as ev, fillrect

WHITE = 0xFFFFFF
BLACK = 0x000000
GREEN = 0x008000
RED = 0xC00000
BLUE = 0x1A5FB4


def txt(y, s, col=BLACK):
    # Quotes are stripped: one inside the expression breaks the PPL line.
    s = str(s).replace('"', "'")[:46]
    ev('TEXTOUT_P("%s",G0,3,%d,2,RGB(%d,%d,%d))'
       % (s, y, (col >> 16) & 255, (col >> 8) & 255, col & 255))


def mark(t):
    """Leave a trace in a PPL global. It is the only thing that survives if
    the app closes: afterwards, in Home, PZ says how far it got."""
    try:
        ev('PZ:="' + t + '"')
    except Exception:
        pass


def check(y, label, expression):
    """One check. If it blows up, it says so instead of taking the app."""
    mark('before: ' + label)
    try:
        r = ev(expression)
        txt(y, '%s = %s' % (label, r), GREEN)
        mark('ok: ' + label)
        return r
    except Exception as e:
        txt(y, '%s FAILED: %s' % (label, str(e)[:20]), RED)
        mark('EXCEPTION: ' + label)
        return None


# The touch wrapper: MOUSE returns lists inside lists, and that cannot cross
# the bridge. Take x, y and the type, and nothing else.
MOUSE = ('LOCAL zm:=MOUSE; LOCAL zp:=zm(1);'
         ' IFTE(SIZE(zp)==0,{-1,-1,-1},{zp(1),zp(2),zp(5)})')

fillrect(0, 0, 0, 320, 240, WHITE, WHITE)
txt(2, 'PROBE', BLUE)

check(22, '1+1', '1+1')                     # does the bridge answer?
check(40, 'list of numbers', '{1,2,3}')     # does a flat list get through?
check(58, 'ticks', 'ticks()')               # the clock, since time is absent
check(76, 'touch wrapper', MOUSE)

# This is where a call to YOUR PPL library goes -- last, because it is the
# one that can kill:
#   check(94, 'MYLIB', 'LOCAL zr:=MYFUNC(3,350); {zr(1),zr(2)}')

txt(112, 'touch the screen or press keys.', BLUE)
txt(130, 'ESC to leave.', BLUE)
ev('DRAWMENU("1","2","3","4","5","6")')

mark('loop')
n = 0
while True:
    try:
        k = ev('GETKEY()')
    except Exception:
        k = -1
    if k == 4:                                # 4 = Esc
        break
    if k is not None and k >= 0:
        fillrect(0, 0, 150, 320, 20, WHITE, WHITE)
        txt(150, 'key: code %d' % k, GREEN)
        mark('key %d' % k)
    try:
        m = ev(MOUSE)
    except Exception:
        m = None
    if isinstance(m, list) and len(m) >= 3 and m[0] >= 0:
        n = n + 1
        fillrect(0, 0, 170, 320, 40, WHITE, WHITE)
        txt(170, 'touch %d:  x=%d  y=%d  type=%d' % (n, m[0], m[1], m[2]),
            GREEN)
        # The soft-key row starts at y=213, and each key is 53 wide.
        button = int(m[0] / 53) + 1 if m[1] >= 213 else 0
        txt(188, 'zone: ' + ('button %d' % button if button else 'list'), BLUE)
        mark('touch %d' % n)

fillrect(0, 0, 0, 320, 240, WHITE, WHITE)
txt(2, 'DONE. touches detected: %d' % n, GREEN if n else RED)
if not n:
    txt(24, 'None: touch does not reach Python.', RED)
    txt(42, 'Drive everything with keys.', BLACK)
mark('done, touches=%d' % n)

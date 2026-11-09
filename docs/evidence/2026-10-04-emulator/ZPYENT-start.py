# ZPYENT - an app whose only Python file is NOT called main.py.
#
#     hpprime build ZPYENT programs/ZPYENT/start.py
#
# Question: apps.main-py, whether the entry point has to be main.py.
# If this file runs, the screen says so in green and PZ on Home says
# "ZPYENT start.py ran". If the app opens and nothing of that happens, the
# name is required. Esc leaves.

from hpprime import eval as ev, fillrect

ev('PZ:="ZPYENT start.py ran"')
fillrect(0, 0, 0, 320, 240, 0xFFFFFF, 0xFFFFFF)
ev('TEXTOUT_P("start.py ran: main.py is not required",G0,3,40,2,'
   'RGB(0,128,0),314)')
ev('TEXTOUT_P("Esc leaves",G0,3,70,2,RGB(0,0,0),314)')

while True:
    try:
        k = ev('GETKEY()')
    except Exception:
        k = -1
    if k == 4:
        break

# 5. Moving to Python

The Prime has carried MicroPython since the 2021 firmware, and with it a bridge
that runs PPL and hands the result back. So the question is not which language
to use, but which half goes where.

The full detail is in [micropython.md](../topics/micropython.md).

---

## When it is worth it

| Move to Python when | Stay in PPL when |
|---|---|
| the interface is getting long | the program is small |
| you already have the logic in Python on your PC | you need a library other programs call |
| you want to test the real code on your PC | you are calling the calculator's own maths |

The reason that outweighs the others is that the file that computes can be
exactly the same on the PC and on the calculator. Only the module underneath
it changes, the one that looks data up, and with that your PC tests say
something real about what runs on the G2
([the architecture](../topics/micropython.md#the-architecture-that-makes-this-useful)).

## Send a probe first

There are questions you cannot answer from a PC: whether the bridge responds,
whether it sees your PPL functions, what `GETKEY` returns for each key, whether
touch arrives and with what coordinates. One app answers all of them in a
single pass:

```bash
hpprime build PROBE examples/probe/main.py -o programs/PROBE
```

Drag it over, open it and read what it reports. It leaves a mark after each
step in order of increasing risk, so if it closes, the last mark says where
([micropython.mark-debugging](../topics/micropython.md#micropython.mark-debugging)).

## Hello, bridge

```bash
hpprime new MYAPP --python
```

That writes `programs/MYAPP/main.py`, with its code at module level rather than inside
an `if __name__` block. Every Python app examined is built that way, with the
file called `main.py` and the code running on import. Whether another name
would work has not been tried, so keep both
([apps.main-py](../topics/apps.md#apps.main-py)).

Everything the screen does goes through the `hpprime` module
([micropython.hpprime-module](../topics/micropython.md#micropython.hpprime-module)),
and PPL through `eval`
([micropython.eval](../topics/micropython.md#micropython.eval)):

```python
from hpprime import eval as ev, fillrect

fillrect(0, 0, 0, 320, 240, 0xFFFFFF, 0xFFFFFF)
ev('TEXTOUT_P("hello",G0,3,10,2,RGB(0,0,0))')
n = ev('1+1')            # -> 2
ev('CX:=3.5')            # write a PPL global
x = ev('CX')             # and read it back
r = ev('CIRCAREA(2)')    # call YOUR PPL library
```

Then build and drag it over:

```bash
hpprime build MYAPP programs/MYAPP/main.py -o programs/MYAPP
```

## The two traps that cost a day each

A list with a string inside closes the app. There is no exception, no message
and no trace: if your PPL function returns `{1, 2, "warning"}`, calling it raw
from Python kills the app on the spot
([micropython.list-with-string-closes-the-app](../topics/micropython.md#micropython.list-with-string-closes-the-app)).

The fix is never to let the raw list out. Wrap the call in PPL and let only
numbers through:

```python
def numbers_only(call):
    return ev('LOCAL zr:=' + call + '; {zr(1),zr(2),zr(3)}')
```

Design your PPL library that way from the start: a flat list of numbers, or a
number.

`time` does not exist. If `import time` fails, the bridge is fine and the
module is simply not there. What MicroPython on the Prime has is `math`,
`hpprime`, `micropython` and not much else
([micropython.modules](../topics/micropython.md#micropython.modules)).
An app that imports a module MicroPython lacks closes at startup, silently,
so `hpprime build` warns about an import it does not recognise
([micropython.imports](../topics/micropython.md#micropython.imports)).

## Debugging when the app closes by itself

There is no trace and the screen is gone. What survives the close is a PPL
global, so leave marks in one:

```python
def mark(t):
    try:
        ev('PZ:="' + t + '"')
    except Exception:
        pass

mark('before the call')
r = ev(EXPRESSION)
mark('call ok')
```

If the app dies, go to Home, type `PZ` and press `[Enter]`. It says how far it
got. Put the marks in order of increasing risk, and the point where it dies
identifies the cause without further experiments
([micropython.mark-debugging](../topics/micropython.md#micropython.mark-debugging)).

## The architecture to aim for

```
      PC                                   calculator
   ---------                            -----------------
   engine.py   \                       /   LIB (PPL)
                >   data.py (2 faces) <
                                       \   hpprime.eval
                       |
                    app.py      <-- THE SAME FILE in both places
                       |
                 main / screen         <-- pixels only here
```

- `app.py` is literally the same file in your repository and in the app.
  `hpprime build` copies it, and `hpprime verify` tells you when the two have
  drifted apart.
- `data.py` is the one piece deliberately written twice, with the same face:
  one version over your PC engine, one over the bridge.
- Whatever touches pixels and keys stays as thin as you can make it, because it
  is the only part you cannot test from the PC.

The detail is in
[micropython.md](../topics/micropython.md#the-architecture-that-makes-this-useful).
A crossing of the bridge costs 0.2 ms, and a calculation making 30 to 40 of
them spends about 8 ms there, so there is nothing to optimise: write the clear
version ([micropython.bridge-cost](../topics/micropython.md#micropython.bridge-cost)).

---

Next: [6. Working with an AI](06-working-with-ai.md).

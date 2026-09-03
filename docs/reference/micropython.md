# Python on the Prime

The Prime has carried **MicroPython** since the 2021 firmware, and with it a
module of its own, `hpprime`, giving direct drawing and -- what really
matters -- an `eval()` that **runs arbitrary PPL and returns the result**.

That makes Python the practical way to write an app's interface and logic,
leaning on PPL only for what the calculator does not expose otherwise. And it
has one consequence worth more than all the rest:

> The file that computes can be **exactly the same** on the PC and on the
> calculator. The only thing that changes underneath is the module that looks
> data up. With that, PC tests say something real about what runs on the G2.

**There is no official HP documentation for any of this.** What follows is
measured on a G2 with firmware 2.4 revision 15515, or read from apps that run
on one. Each item says which.

---

## 1. What is there and what is not

Confirmed by running it on the calculator:

| | |
|---|---|
| `math` | **yes** -- and it is the whole library dependency a calculation engine needs |
| `hpprime` | **yes** -- the bridge and the drawing |
| `micropython` (`const`) | yes |
| **`time`** | **DOES NOT EXIST.** Apps that need it bring their own `time.py` built on `eval('ticks()')` |
| `__future__` | no |
| `os`, `sys` | not in the CPython sense: do not count on them |
| NumPy | no. For linear algebra, the route is the Prime's own `linalg` *(community, not measured here)* |

The missing `time` is a diagnosis worth knowing about, because of how it
fails: `import time` raises, and it is easy to conclude that the Python
bridge does not work at all. It does. The way to find out is to read an app
that runs on that same calculator -- the Markdown Viewer starts literally
with `from hpprime import eval, fillrect`.

**Method, not trivia**: when something fails on a badly documented platform,
find code that already works *on that same machine* before concluding
anything.

> Modules the community documents that are **not** measured here: `cmath`,
> `array`, `gc`, `sys`, `ucollections`, `uerrno`, `uhashlib`, `uio`,
> `urandom`, `ure`, `ustruct`, `utimeq`, and the `graphic` and `cas`
> (`cas.caseval`) modules. Source:
> [HP Prime Python Libraries](https://udel.edu/~mm/hp/primePython/upython.html).
> That same source warns that the Prime implements **a subset** of
> MicroPython, and that more routines are documented than exist.

## 2. The `hpprime` module

```python
from hpprime import eval, fillrect, keyboard
```

What is **in use and working** in apps that run on this calculator:

| Call | What it does |
|---|---|
| `eval(ppl_string)` | runs PPL and returns the result (§3) |
| `fillrect(gr, x, y, w, h, edge, fill)` | filled rectangle. `gr=0` is the screen |
| `keyboard()` | true if any key is down |
| `dimgrob(n, w, h, colour)` | creates an off-screen grob (used to measure text) |

Colours are 24-bit integers, `0xRRGGBB`.

> The community documents plenty more: `arc`, `blit`, `circle`, `grob`,
> `grobh`, `grobw`, `line`, `mouse`, `pixon`, `rect`, `strblit`, `textout`,
> `get_cartesian`, `set_cartesian`, and a `_c` variant of each. They are not
> measured here, and for nearly all of them there is a PPL equivalent
> reachable through `eval`, which is what the apps read here do.

## 3. The bridge: `eval()`

The heart of it. You build a string of PPL and run it:

```python
from hpprime import eval as ev

ev('TEXTOUT_P("hello",G0,10,20,2,RGB(0,0,0))')   # draws
n = ev('1+1')                                     # -> 2
t = ev('ticks()')                                 # milliseconds
ev('CX:=3.5')                                     # writes a PPL global
x = ev('CX')                                      # and reads it back
r = ev('MYFUNC(1.0)')                             # calls YOUR PPL library
```

**It returns numbers and lists of numbers.** That is all you need to call a
well-written PPL library.

### The trap that closes the app

This is measured, and it is not a precaution: it is the difference between
working and the app vanishing.

> **A list with a string inside closes the app.** No exception, no message,
> no trace.

A function returning `{T,P,v,u,h,s,x,region,WARNING}` -- eight numbers and a
text warning at the end -- called raw from Python **closes the app**.
Everything that had worked until then returned plain numbers.

The fix is never to let the raw list out: wrap the call in PPL and only let
numbers through.

```python
def _eight(call):
    """Run a PPL call and take ONLY the eight numbers. The warning -- the
    ninth element, which is text -- is dropped in here."""
    return ev('LOCAL zr:=' + call + '; {zr(1),zr(2),zr(3),zr(4),zr(5),'
              'zr(6),zr(7),zr(8)}')
```

The same pattern covers `MOUSE`, which returns **lists inside lists**:

```python
_MOUSE = ('LOCAL zm:=MOUSE; LOCAL zp:=zm(1);'
          ' IFTE(SIZE(zp)==0,{-1,-1,-1},{zp(1),zp(2),zp(5)})')
```

**General rule**: have the PPL wrapper always return a flat list of numbers,
or a number. If your PPL library is going to be called from Python, design it
that way from the start.

### Building the string without breaking it

Two rules that came out of using it:

**Quotes.** One quote inside the string breaks the PPL expression. Clean them
before concatenating:

```python
s = str(s).replace('"', "'")
```

**Numbers.** A number Python writes in scientific notation with a `+` sign --
`1e+20` -- is what the Prime's HOME environment misreads *(reported by the
community, not measured here; the workaround they propose is `cas.caseval`)*.
What is in use and works is passing numbers through `repr(float(x))`, which
in the normal working range gives a form the PPL parser understands:

```python
def _n(x):
    """A number into PPL text, without notation the parser will not take."""
    return repr(float(x))
```

If you are going to move very large or very small magnitudes, check it with a
probe before trusting it.

### What it costs

**0.2 ms per crossing**, measured. A calculation making 30-40 lookups spends
about **8 ms** on the bridge. There is nothing to optimise: write the clear
code and cross as often as you need.

## 4. The architecture that makes this useful

The bridge on its own is not much. What turns it into a serious way of
working is this split:

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

- **`app.py` is the same file** in the repository and in the app. It is
  copied with a command, and a check confirms they have not drifted apart
  (`hpprime verify`).
- **`data.py` has two versions with the same face.** One calls the PC engine,
  the other crosses the bridge. It is the one piece deliberately duplicated.
- **Whatever touches pixels and keys is isolated in a module as thin as you
  can make it**, because it is the only part that cannot be tested from the
  PC.

That discipline pays: a synchronisation test of this kind is what catches a
serialised form that silently drops a field. On the Python side a round trip
can pass because the defaults happen to match; the PPL side, which has no
defaults, gives it away at once.

### Imports in shared files

A module that goes to the calculator can only import what MicroPython has.
It is worth a test, because the symptom on the calculator is that **the app
closes without a word**:

```python
ALLOWED = ('math', 'engine', 'data', 'list', 'views', 'screen', 'hpprime')
```

Imports inside a function do not count: only top-level ones. `hpprime build`
checks this for you.

And **delete `__pycache__`** before packaging: CPython `.pyc` files
MicroPython would not read.

## 5. Debugging when the app closes by itself

No trace, no message, and the screen is gone. The technique that works is to
**leave a mark in a PPL global**, which survives the close:

```python
def mark(t):
    try:
        ev('PZ:="' + t + '"')
    except Exception:
        pass

mark('before the wrapper')
r = ev(EXPRESSION)
mark('wrapper ok')
```

If the app closes: go to **Home**, type `PZ` and press `Enter`. It says
exactly how far it got.

That is how the §3 trap was found in a single pass. The probe tried things
**in order of increasing risk** -- `{1,2,3}`, then `{1,"a"}`, then a real
list of ten numbers, then the trimmed call, and the raw one last, because
that was the one that killed it -- so the exact point where it died
identified the cause with no further experiments.

**Package the probe as an app**, not as a loose script: that way it runs by
the same path the real app will, and you are not measuring something else.

There is one ready to adapt in [examples/probe/](../../examples/probe/). It
answers in one pass what cannot be answered from the PC -- whether the bridge
responds, whether it sees your PPL functions, what `GETKEY` returns for each
key, whether touch arrives and with what coordinates -- and it is the first
thing worth putting on a calculator before writing the real app:

```bash
hpprime build PROBE examples/probe/main.py
```

## 6. From PPL into Python

The reverse direction exists: PPL can run a Python script with

```ppl
PYTHON("script_name", parameters);
```

and the program editor accepts `#PYTHON … #END` blocks inside PPL source.

*Not measured in this kit* -- it has not been needed, because for a
calculation engine the useful direction is the other one. It is here so the
door is on record. Source:
[HP Prime Programming](https://udel.edu/~mm/hp/primePython/).

## 7. Still not measured

- **Pure computation speed in Python** against PPL. The bridge crossing is
  measured (§3); how long a long numeric loop takes inside MicroPython is
  not.
- **The memory limit** of a Python app: how many modules, and how large,
  before it runs out of room.
- **The `_c` variants and the rest of the `hpprime` module**: anything not in
  §2 has not been exercised here.

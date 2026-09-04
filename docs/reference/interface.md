# Screen, keyboard and touch

320 × 240 pixels, a keyboard whose codes are not ASCII, a touch screen and no
window manager. The official documentation describes the commands one by one
and says nothing about how they combine, so nearly everything here comes from
**measuring it on a G2** or from **reading apps that run on one**.

It applies to both languages: from PPL you call these directly, and from
Python you call the same things across the `hpprime.eval` bridge (see
[micropython.md](micropython.md)).

---

## 1. The geometry

| | |
|---|---|
| Screen | **320 × 240** |
| App area | y from **0 to 212** |
| Soft-key row | y from **213 to 239** |
| Width of one soft key | ~**53 px** (320 / 6) |

The last two are measured, and they are what turns a touch into a button:

```python
def soft_key_at(x, y):
    """Which soft key was touched, or 0 if the touch is not in that row."""
    if y < 213:
        return 0
    n = int(x / 53) + 1
    return n if 1 <= n <= 6 else 0
```

A layout that works well for a list: a 20 px header, seven 24 px rows, and
the help line underneath.

## 2. The building blocks

| What you need | Command |
|---|---|
| Clear the screen | `RECT()` · from Python, `fillrect(0,0,0,320,240,col,col)` |
| Rectangle | `fillrect(gr, x, y, w, h, edge, fill)` |
| Text | `TEXTOUT_P(txt, G0, x, y, font, colour [, width])` |
| A row of six buttons | `DRAWMENU("a","b","c","d","e","f")` |
| Form | `INPUT(fields, title, labels, help)` |
| Pop-up menu | `CHOOSE(var, title, "opt1", "opt2", …)` |
| Modal notice | `MSGBOX("message")` |
| Pending key | `GETKEY` |
| Touch | `MOUSE` |
| Flicker-free drawing | `DIMGROB_P` to an off-screen grob, then `BLIT_P` to `G0` |

`TEXTOUT_P` fonts: 1 small, 2 normal, 3 large (up to 7). Colours with
`RGB(r,g,b)` in PPL, `0xRRGGBB` integers from Python.

## 3. `TEXTOUT_P` clips -- and without being asked, it overflows

The seventh argument of `TEXTOUT_P` is the **maximum width in pixels**.
Without it, a long string is written over the neighbouring column and keeps
going until it runs off the screen.

Here is what makes that dangerous:

> **Text that does not fit raises no error.** The calculator cuts it or
> paints it over something else, and you never learn what it said.

Three things close the hole:

1. **Always pass the width.** With it, a long string is at worst truncated,
   but stays inside its column.
2. **Long help text on its own line**, with all 320 pixels, changing with the
   cell you are on. A third column has about 70 pixels.
3. **A geometry module with no imports at all**, holding every column's `x`,
   so a PC test can read it and check screen by screen that each string fits
   where it goes.

**The width is the last argument of whichever form you use**, measured on a
G2 by drawing one long string three times:

```ppl
TEXTOUT_P(txt, x, y, font, colour, width)          // clips at width
TEXTOUT_P(txt, G0, x, y, font, colour, width)      // clips at width
TEXTOUT_P(txt, x, y, font, colour)                 // runs off the screen
```

`hpprime lint` catches the missing one for you, in both forms
(`textout-width`).

Character widths in such a test should be **deliberate over-estimates**: take
the widest character, so that when the test says it fits, it fits. The
converse does not hold.

If you ever need to measure for real, the way is the one the Markdown Viewer
uses: `TEXTOUT_P` **returns the x where it finished**, so drawing onto an
off-screen grob gives you the exact width.

```python
def text_width(txt, fnt=2):
    dimgrob(9, 512, 22, 0)
    return eval('textout_p("' + txt + '",G9,0,0,0,0)')
```

## 4. `INPUT`: what to know before designing around it

```ppl
zok := INPUT(
  { {CUR, NAMES, {22, 72, 0}},                         // a drop-down
    {D1, PROPS, {22, 30, 1}}, {V1, [0], {58, 37, 1}},  // two fields, one row
    {D2, PROPS, {22, 30, 2}}, {V2, [0], {58, 37, 2}} },
  "Which two do you know?",
  {"Subst", "Datum 1", "=", "Datum 2", "="},
  {"substance", "1st known quantity", "value, in the unit shown",
   "2nd known quantity", "value, in the unit shown"});
```

It returns **1 if accepted, 0 if cancelled**. What is measured:

| | |
|---|---|
| **Field position** | `{x%, width%, row}`, as a **percentage** of the screen |
| **The label sits to the left of the field** | at `x=5` labels came out clipped to a dot; at `x=22` they fit |
| **Field type** | `[0]` is real: the number is typed as it is, **with no quotes** |
| **A text field demands quotes** | typing `"0.2"` under exam pressure is a tax on every value |
| **It is modal and builds its labels once** | a label that depends on another field of the same form **cannot be refreshed** |
| **The variables must already exist, with the right type** | |

That quotes detail decides whole interfaces. Given a choice between a form
with blank cells (which needs **text** fields, so quotes) and two drop-downs
plus two numeric fields, the drop-downs win: they say **what** you know, the
numeric fields say **how much**, and the label can show the unit. The form
with blanks looks better on paper and is worse on the machine.

### One-field `INPUT`, not a form of ten

From Python, for two reasons you do not see until you use it:

```python
def ask(title, label, value):
    """One field. Returns the new value, or None if cancelled."""
    ev('CX:=%s' % repr(float(value)))
    r = ev('INPUT(CX,"%s","%s","")' % (title, label))
    if not r:
        return None
    return ev('CX')
```

- You can **correct one value** without walking through the other nine.
- Labels **can depend on context** -- the unit for that particular row, say
  -- which a large `INPUT` cannot do, because it builds them once.

## 5. The keyboard

### `GETKEY` returns a position, not a character

This is the first thing that trips people: the code for `[Enter]` is **30**,
not 13. And the same code means different things in different modes -- 42 is
`1` in normal mode and `y` in alpha mode.

**A code is a position, counted along the keyboard from the top left.** The
whole map, 51 keys, codes 0 to 50:

| Where | Codes |
|---|---|
| top block | `Apps` **0**, `Symb` **1**, ▲ 2, `Help` **3**, `Esc` 4 |
| | `Home` **5**, `Plot` **6**, ◄ 7, ► 8, `View` **9** |
| | `CAS` **10**, `Num` **11**, ▼ 12, `Menu` **13** |
| keypad, **six** wide | `Vars` **14**, Mem 15, Units 16, `x t θ n` 17, `a b/c` 18, `Del` 19 |
| keypad, **six** wide | `x^y` 20, `SIN` 21, `COS` 22, `TAN` 23, `LN` 24, `LOG` 25 |
| keypad, five wide | `x²` 26, `+/-` 27, `( )` 28, `Eval` 29, **`Enter` 30** |
| | `EEX` 31, **7 32**, **8 33**, **9 34**, `÷` 35 |
| | `ALPHA` 36, **4 37**, **5 38**, **6 39**, `×` 40 |
| | `Shift` 41, **1 42**, **2 43**, **3 44**, `−` 45 |
| | `On` 46, `0` 47, `.` 48, space 49, `+` **50** |

Bold is measured by pressing the key. `Esc`, the arrows, `Del`, `On` and the
digits come from two working apps that agree. The rest is **derived**: the
codes are contiguous, so once the ends of a row are known the keys between
them follow from the keyboard's own layout -- read off the machine, not
guessed at.

**The rows are not all the same width**, and that is the part worth
remembering: the two top rows of the white keypad have **six** keys, the five
below them have five. An earlier version of this page assumed five
everywhere. It fitted the digits by luck and could not explain why 50, the
last code, sits at the bottom right instead of starting another row. With the
real layout, 14 + 6 + 6 + 5×5 = 51 keys and the last one is `+` at 50, which
is exactly where it is.

Nothing known contradicts this map: eleven keys measured directly and eleven
read from other people's code all land on it.

### The six on-screen labels are not keys

Two published apps map "soft keys 1..6" to the codes **0, 5, 10, 1, 6, 11**.
Now that those codes have names, that is `Apps`, `Home`, `CAS`, `Symb`,
`Plot`, `Num`: the **top-left 3×2 block of physical keys**, taken column by
column.

They have to be physical keys, because of the other half of the measurement:

> **Touching the six labels along the bottom of the screen reports nothing
> through `GETKEY`.** Measured on a G2. They are touch targets, and touch
> arrives through `MOUSE` (§6).

So if your program wants those labels driven from the keyboard as well as by
finger, you pick the physical keys yourself, and the block above is what
other people picked.

> **In a blank-based app, `[Num]` and `[View]` do reach your program** --
> as ordinary key codes, through `GETKEY`. What does not happen is the
> `Num()` and `View()` hooks being called, because `START()` is holding the
> keyboard. Measured on a G2 in an app built by this kit. It is what makes
> the recommended workaround -- draw your own menu, read the keys yourself --
> actually work. See [apps.md](apps.md#5-ppl-apps-the-hooks-and-the-blank-app-trap).

Which physical key carries which code below row 2 has been measured only for
the ones named above. [examples/keymap/](../../examples/keymap/) prints any
of them in one run: it shows the code of every key you press until you leave
with `Esc`.

**Design to fail quietly**: send an unknown key code to the default case, and
make that case something harmless like returning to the previous screen. A
three-line program tells you the code of whatever you press:

```ppl
EXPORT TKEY()
BEGIN
  LOCAL zk;
  RECT(); TEXTOUT_P("Press a key...", 4, 40, 3);
  zk := TPAUSE();
  RECT(); TEXTOUT_P("code = " + STRING(zk), 4, 40, 4);
  TPAUSE();
  RETURN zk;
END;
```

### A program that draws and returns loses its screen

Measured on a G2: run a program from Home, have it draw with `TEXTOUT_P` and
then `RETURN`, and what you are left looking at is **Home, with the return
value**. The drawing does not survive the program ending.

So anything meant to be read has to wait before it returns:

```ppl
  TEXTOUT_P("press a key to leave", 2, 206, 2);
  MYWAIT();          // drain, then wait -- see below
  RETURN 1;
```

This is the first thing that goes wrong with a diagnostic program, and it
looks like the program did nothing at all.

What you are left with instead is a framed line in the Home history, with the
program's name and the value it returned:

```
 (i)  SPROBE2 1
```

It is not a message: **it is the return value**, shown the way Home shows the
value of anything you type, and it behaves like any other history entry.

Which means you cannot switch it off by leaving `RETURN` out. Measured: a
function with no `RETURN` at all still put a number there -- the value of its
last bare expression, which was a call to another function.

**Where** it appears depends on how the program was started:

| Started from | What you get |
|---|---|
| **Home** | a line in the history: the program's name and the value |
| **the Program Catalog** | a modal pop-up with an information icon, saying the same |

**Nothing suppresses it.** Measured, five endings: an assignment, a loop, an
`IF` that does not run, a call, and a bare `RETURN;`. Every one of them
answers with a number, so every one of them leaves a line. What you choose is
what the number says, not whether it appears --
[ppl.md](ppl.md#a-function-always-answers-something).

### Waiting for a key: drain the buffer first

There is a measured contradiction here, worth knowing before you choose:

> **In one program, `WAIT(-1)` did not wait.** A results screen flashed past
> and the form came straight back. It looked like it was waiting, because
> that program was called from another one and the screen survived until the
> next redraw; once a loop was added, it was clear it had not. (Returning to
> **Home** is different: there the screen is gone at once, see above.)
>
> **In two published apps, `WAIT(-1)` is the event loop**: it returns a
> number (key) or a list (touch), and returns −1 every 60 s.

The likeliest explanation -- **hypothesis, not measurement** -- is a key
still pending in the buffer: the one that had just accepted the `INPUT`.
Either way, what **does** work on this calculator is to drain, then wait:

```ppl
EXPORT TPAUSE()
BEGIN
  LOCAL zk;
  REPEAT zk := GETKEY; UNTIL zk < 0;    // drain what is pending
  REPEAT zk := GETKEY; UNTIL zk >= 0;   // and only now wait
  RETURN zk;
END;
```

From Python the same principle with `keyboard()` + `GETKEY()`:

```python
if keyboard():
    k = ev('GETKEY()')
```

`WAIT(-1)` would use less battery and deliver touches in the same place. If
you use it, **check it yourself**.

## 6. Touch, and the touch that arrives twice

`MOUSE` returns **lists inside lists**: `{{x1,y1,x0,y0,type}, …}`. From
Python it has to be flattened before it crosses the bridge, because a list
that is not all numbers **closes the app** (see
[micropython.md](micropython.md)):

```python
_MOUSE = ('LOCAL zm:=MOUSE; LOCAL zp:=zm(1);'
          ' IFTE(SIZE(zp)==0,{-1,-1,-1},{zp(1),zp(2),zp(5)})')
```

### The failure you cannot see by reading the code

> The Prime's dialogs (`INPUT`, and notices) are accepted with an **OK button
> that falls right on top of the soft-key row, in the F6 position**. If your
> finger is still there when the dialog closes, **the same touch arrives
> again** at the screen underneath, as though you had pressed its F6.

The fix is a debounce **with memory**, and it belongs in the pure-logic
module -- not in the pixel one -- precisely so it can be tested on the PC:

```python
class Debounce(object):
    """One touch = one action."""

    def __init__(self):
        self.touching = True

    def purge(self):
        """Count as touched: the touch that closes one thing does not count
        in the next."""
        self.touching = True

    def passes(self, touching_now):
        """True only on the first contact of a new touch."""
        if not touching_now:
            self.touching = False
            return False
        if self.touching:
            return False
        self.touching = True
        return True
```

Call `purge()` when closing **any** dialog and on returning from **any**
screen, so no single place can forget. It solves two different things at
once: the screen is read dozens of times a second while a finger stays down,
and the touch that closes a dialog outlives the dialog.

## 7. One widget for everything: the windowed list

The design finding that saves the most work. A list with seven visible rows,
a top index, a scrollbar, arrows, touch and digit jump covers nearly every
screen a calculation app has:

| Screen | What a row is |
|---|---|
| The data | one record: `3   0.800   26.0   236.0` |
| The parts | one component: `2  HEATEX  2 -> 3` |
| The results | one solved record |
| The diagnosis | what is missing: `Record 7: T, h, s missing` |

Writing it once and using it four times is the difference between an
interface that fits your budget and one that does not. And since it is
**pure logic** -- selection, window, bar, what each key means -- it can be
tested entirely on the PC. The pixel module is left with drawing rows.

### Behaviour worth copying as it is

All of this comes from apps that work, not from invention:

- **Digits jump to a row.** Pressing `7` goes to row 7 instead of pressing
  down seven times. Under exam pressure this is what people notice.
- **Selection wraps** at the ends.
- **Left and right change column** when there are several, and page when
  there are not. That is what the calculator's own Numeric view does, so the
  gesture is already known.
- **Touching a row selects it; touching it again enters.** That is how the
  system's own lists behave.
- **`Cancel` and `OK` in positions 5 and 6** of the soft-key menu. Platform
  convention.
- **Partial redraw**: moving the selection repaints two rows, not the screen.
- **Automatic exit on inactivity.** In an exam, battery matters.
- **`IFERR` around the event loop**, draining the queue if it fires.
- **A two-page soft menu** when you need more than six actions, rather than
  cramming six unreadable labels.
- **Theme colours**, so it does not clash in dark mode.

What is **not** worth copying is a full event framework with drags, long
press and eight handlers. For an app driven by arrows, `Enter` and six
buttons, it is dead weight.

## 8. A table needs no sentinels; a form does

An obvious first move is a form: `Enter` on a record opens an `INPUT` with
four fields. It is fast, and it is wrong, for a reason you only see in use:

> A form cannot say *"I do not know this one"*.

You end up inventing sentinels: `0` means empty, and since `0` is a
legitimate value you need a separate `-1`. Even then a real zero cannot be
typed.

An **editable table** does not have the problem. An empty cell is empty:

```
  RECORDS                                   4 records
   #      P        T        x       deg
 +----+--------+--------+--------+--------+
 | 1  | 0.1    |   -    |   -    | 6.36   |
 | 2  | 0.8    |  60    |   -    |   -    |
 | 3  | 0.8    |   -    |   -    | -5.33  |
 | 4  | 0.1    |   -    |   -    |   -    |
 +----+--------+--------+--------+--------+
  1.P  pressure  [MPa]
 [HowMany][Fluids][Fluid][Clear][Back][h s v u]
```

Two details that only come out of typing a real problem into it:

- **After editing, the cursor moves down on its own.** Data arrives by
  column -- one sentence often gives the same quantity for two records -- so
  a column gets filled in one go.
- **Defaults are proposed.** When the output of one part is the input of the
  next, proposing it means a four-part chain is typed without entering a
  single connecting number.

## 9. Units are not asked for; they are stated

A reasonable question when looking at a properties screen: *"how does the app
know whether I am in °C or K?"* The answer is that it must not be a choice.

> Asking at startup would be worse than saying nothing: it lets somebody
> enter `25` where the table expects `298`, and the result comes out
> **solved and wrong**, which is the worst way to fail because nothing warns
> you.

Derive the unit from the data, and show it: in the `INPUT` label, in the help
line, and in the column title when a whole column shares one. When they do
not share one, keep the title neutral and put the unit in the help line,
which does belong to the row you are on.

## 10. What can be tested on the PC, and what cannot

This is the division that orders everything above:

| | Tested on the PC | Only on the calculator |
|---|---|---|
| Selection, window, bar, what each key does | yes | |
| What text goes in each row | yes | |
| That each string fits its column | yes (against the geometry module) | |
| Drawing, reading keys, reading touch | | no |
| That a dialog closes where you think | | no |
| How long a real data entry takes | | no -- time it |
| Whether the calculation behind it is fast enough | | no -- see speed in [ppl.md](ppl.md) |

To size a screen before drawing it: with the small font, of the order of
**20 rows of 40 characters** fit -- an estimate, not a measurement, so use it
to rule a design out, not to call one good.

This is why the pixel module should be **as thin as you can make it**:
everything deciding *what* is shown and *what* happens lives outside it.

The kit's interpreter follows the same rule: `TEXTOUT_P`, `INPUT`, `CHOOSE`,
`MSGBOX` and `WAIT` are **not drawn**; they are recorded in `machine.io` and
return a neutral value, so the calculation runs with no interface.

## 11. Where this comes from

Third-party apps read from [hpcalc.org](https://www.hpcalc.org/prime/), all
of them running on real calculators:

| Program | What it contributed |
|---|---|
| **SkeletonApp** (Andreas Möller) | the event loop and the soft-menu geometry |
| **CHOOSE_R 1.0** (Jacob Wall) | the windowed list, partial redraw, inactivity exit |
| **LibMenu 3.0** | the two-page soft menu |
| **ktest** / **WaitLab** | what each input method returns, exactly |
| **CAC** | the "choose what you are solving and only be asked for what it needs" pattern |
| **Markdown Viewer** | the `keyboard()` + `GETKEY()` loop from Python, and measuring text with a grob |
| **PrimeEdit** | proof that a full interface fits in Python: widgets, menus, icons, syntax highlighting |

The rest is measured on a **G2 with firmware 2.4 revision 15515**.

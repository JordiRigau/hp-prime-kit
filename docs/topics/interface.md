# Screen, keyboard and touch

Facts about the machine a program draws on and reads from, rather than about
one command. Each has an identifier, says how it is known, and is stated here
once.

320 × 240 pixels, a keyboard whose codes are not ASCII, a touch screen and no
window manager. HP's documentation describes the commands one by one and says
nothing about how they combine, so nearly everything here comes from measuring
it on a G2 with firmware 2.4.15515, or from reading apps that run on one --
and which of the two is the label on each fact.

It applies to both languages: from PPL you call these directly, and from
Python you call the same things across the `hpprime.eval` bridge
([micropython.md](micropython.md)).

## The building blocks

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

`TEXTOUT_P` fonts: 1 small, 2 normal, 3 large, up to 7. Colours with
`RGB(r,g,b)` in PPL, and `0xRRGGBB` integers from Python. From Python the two
grob calls are `dimgrob(1, 320, 240, 0)` and `blit(0, 0, 0, 1)`, read from a
published toolkit that creates the grob once when it loads and blits every
frame.

## What the design of a screen comes down to

How a screen is designed is the app's own choice. Ways apps that work have done
it, with what each costs, are in [patterns.md](../patterns.md); this page holds
what any design runs into.

**What can be tested on the PC**: any function that decides without drawing,
such as what text goes in each row and whether it fits its column. What
cannot: drawing, reading keys, reading touch, whether a dialog closes where
you think, how long a real data entry takes, and whether the calculation
behind it is fast enough ([ppl.md](ppl.md#ppl.speed-anchor)). The interpreter
on the PC records `TEXTOUT_P`, `INPUT`, `CHOOSE`, `MSGBOX` and `WAIT` in
`machine.io` and returns a neutral value, so a calculation runs with no
interface.

Before building a scrolling list or a menu with pages, see
[libraries.md](libraries.md): which of the three levels a screen
needs, and what the third-party libraries `CHOOSE_R`, `LibMenu` and
`SkeletonApp` already give you.

## Where this comes from

Third-party apps read from [hpcalc.org](https://www.hpcalc.org/prime/), all of
them running on real calculators:

| Program | What it contributed |
|---|---|
| **SkeletonApp** (Juerg W. Buser) | the event loop and the soft-menu geometry |
| **CHOOSE_R 1.0** (Jacob Wall) | the windowed list, partial redraw, inactivity exit |
| **LibMenu 3.0** | the two-page soft menu |
| **ktest** / **WaitLab** | what each input method returns, exactly |
| **CAC** | the "choose what you are solving and only be asked for what it needs" pattern |
| **Markdown Viewer** | the `keyboard()` + `GETKEY()` loop from Python, and measuring text with a grob |
| **PrimeEdit** | proof that a full interface fits in Python: widgets, menus, icons, syntax highlighting |

The rest is measured on a G2 with firmware 2.4 revision 15515.

---

<a name="interface.geometry"></a>
## The screen is 320x240, and the soft-key row is the bottom 27 pixels

| | |
|---|---|
| Identifier | `interface.geometry` |
| Kind | rule |
| Known from | G2 |

| | |
|---|---|
| Screen | 320 × 240 |
| App area | y from 0 to 212 |
| Soft-key row | y from 213 to 239 |
| Width of one soft key | ~53 px (320 / 6) |

That is what turns a touch into a button: below y 213, the key is
`int(x / 53) + 1` when that lands in 1..6.

**Evidence.** The app area and the soft-key row were measured on a G2 with
firmware 2.4.15515; the key width is the arithmetic that follows from six
across 320 pixels.

---

<a name="interface.draw-units"></a>
## A drawing unit is ten pixels, and the origin is the middle of the screen

| | |
|---|---|
| Identifier | `interface.draw-units` |
| Kind | rule |
| Known from | emulator |

The commands that come in two forms -- `LINE` and `LINE_P`, `DIMGROB` and
`DIMGROB_P`, `GROBW` and `GROBW_P` -- do not differ in what they draw but in
what their numbers mean. The `_P` forms count pixels from the top-left corner.
The forms without `_P` count the current view's units from the middle of the
screen, and in the view a program starts with, one unit is ten pixels.

The conversion in that view is `px = 160 + 10x` and `py = 109 - 10y`, with y
running upwards while pixels run down. The screen is 32 units across, x from
-16 to 16.

This is why a picture sized with the wrong form comes out ten times too big,
and why `GROBW` and `GROBW_P` disagree by a factor of ten on the same grob.
When you mean pixels, use the `_P` form.

**All of that is the plot window a reset calculator has, and it moves with
the window.** The units are the active app's
[Xmin](../commands/common-plot-view/Xmin.md) to
[Xmax](../commands/common-plot-view/Xmax.md) and
[Ymin](../commands/common-plot-view/Ymin.md) to
[Ymax](../commands/common-plot-view/Ymax.md), −15.9 to 15.9 by
−10.9 to 10.9 there. With `Xmin` set to 0, `C→PX(0,0)` answered
`{1,109}`; with `Ymax` set to 0, `{160,0}`. A program that draws in units
draws somewhere else once anything has changed the window, which the `_P`
forms never do.

**Evidence.** On the Virtual Calculator 2.4, build 2025-09-15:
`C→PX(0,0)` answers `{160,109}` and `C→PX(1,1)` answers `{170,99}`;
`PX→C(0,0)` answers `{-16,10.9}` and `PX→C(100,50)` answers `{-6,5.9}`;
a grob made `DIMGROB(G4,10,5,0)` measures 100 through `GROBW_P`
([results.tsv](../commands/results.tsv)). The window's rows were measured on
the same build on 2026-09-24, with the Function app active and each value
put back inside its row.

<a name="interface.offscreen-grob"></a>
## Drawing straight onto the screen shows the work

| | |
|---|---|
| Identifier | `interface.offscreen-grob` |
| Kind | rule |
| Known from | unverified |

Rows appear one at a time and a redraw blinks. Draw into an off-screen grob
and copy the finished picture across in one go:

```ppl
DIMGROB_P(G1, 320, 240, 0);     // a canvas the size of the screen
// ... draw into G1 ...
BLIT_P(G0, G1);                 // one copy, one visible change
```

`G0` is the screen; `G1` through `G9` are yours.

**Evidence.** Seen on a G2 with firmware 2.4.15515, with no program kept. The
Python equivalent, `dimgrob` and `blit`, is read from a published toolkit rather than
measured here.

<a name="interface.two-themes"></a>
## There are two themes, and in the dark one RECT() leaves black text unreadable

| | |
|---|---|
| Identifier | `interface.two-themes` |
| Kind | rule |
| Known from | emulator |

The calculator has a light colour theme and a dark one, and the first
number of [Theme](../commands/system/Theme.md) is 2 in the dark one. There,
`RECT()` clears the screen to RGB(25,25,25), not to white, and `TEXTOUT_P`
with no colour given writes in a light grey, about RGB(235,235,235). Black
given as the colour, on what `RECT()` left, is black on near-black: it can
hardly be read. On a rectangle the program fills white itself, black reads
as well as anywhere, and so do white on black, black on grey, and red, green
and blue on white.

So a program that names its text colour has to name the background too, by
filling it, rather than leave the background to `RECT()` and the theme.
Published apps keep two sets of colours -- background, foreground,
selection, and one per state -- and pick a set at startup (unverified: read
from those apps), and this is why.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, on 2026-10-04, with the theme set to dark by
hand. One program cleared with `RECT()`, printed `STRING(EXPR("Theme"))` in
black, which read `{#2:64h,#5:64h}`, printed a line with no colour given,
and filled six rectangles with `RECT_P` to draw black on white, white on
black, black on grey, and red, green and blue on white. The colours above
were read from the pixels of a screenshot of it. The same program in the
light theme was not photographed; a reset calculator answers
`{#1:64h,#5:64h}`, which is taken to be the light one (unverified).

The test programs are in [docs/evidence](../evidence/README.md#interface.two-themes).

<a name="interface.textout-width"></a>
## TEXTOUT_P overflows unless you pass the width

| | |
|---|---|
| Identifier | `interface.textout-width` |
| Kind | rule |
| Known from | G2 |

The last argument is the maximum width in pixels. Without it, a long string is
written over the neighbouring column and keeps going until it runs off the
screen, and nothing raises an error: the calculator cuts the text or paints it
over something else, and you never learn what it said.

```ppl
TEXTOUT_P(txt, x, y, font, colour, width)          // clips at width
TEXTOUT_P(txt, G0, x, y, font, colour, width)      // clips at width
TEXTOUT_P(txt, x, y, font, colour)                 // runs off the screen
```

Three things close the hole: always pass the width; put long help text on its
own line with all 320 pixels; and keep a geometry module with no imports at
all, holding every column's `x`, so a PC test can check screen by screen that
each string fits. Character widths in such a test should be deliberate
over-estimates -- take the widest character -- so that when the test says it
fits, it fits.

**Evidence.** Measured on a G2 with firmware 2.4.15515 by drawing one long
string in the three forms above. `hpprime lint` catches the missing argument
in both forms, as `textout-width`.

<a name="interface.text-measure"></a>
## TEXTOUT_P returns the x where it finished, which is how text is measured

| | |
|---|---|
| Identifier | `interface.text-measure` |
| Kind | rule |
| Known from | unverified |

Drawing onto an off-screen grob and reading the return value gives the exact
width of a string, which no other call reports.

```python
def text_width(txt, fnt=2):
    dimgrob(9, 512, 22, 0)
    return eval('textout_p("' + txt + '",G9,0,0,0,0)')
```

**Evidence.** Read from the Markdown Viewer's source, which uses it that way.
Not measured here: one program drawing a known string and printing the return
value would settle it.

<a name="interface.font-glyphs"></a>
## Some arrow characters come out of TEXTOUT_P as an empty box

| | |
|---|---|
| Identifier | `interface.font-glyphs` |
| Kind | rule |
| Known from | emulator |

The font has no glyph for some characters. `TEXTOUT_P` draws an empty box in
their place and raises no error, so a program looks right in its source and
wrong on the screen. Eight left and right pairs, in font 3:

| Left | Right |
|---|---|
| ◄ U+25C4: **empty box** | ► U+25BA: drawn |
| ◀ U+25C0: drawn, a small triangle | ▶ U+25B6: drawn, a small triangle |
| ← U+2190: drawn | → U+2192: drawn |
| ◂ U+25C2: **empty box** | ▸ U+25B8: **empty box** |
| ⇐ U+21D0: drawn | ⇒ U+21D2: drawn |
| ⯇ U+2BC7: **empty box** | ⯈ U+2BC8: **empty box** |
| « U+00AB: drawn | » U+00BB: drawn |
| `<`: drawn | `>`: drawn |

In font 2, ▲ U+25B2, ▼ U+25BC, ° U+00B0 and ω U+03C9 are drawn.

The first row is the trap: one half of a pair can be missing while the other
is there, so seeing ► on the screen says nothing about ◄. Write ◀ ▶, or ← →,
rather than ◄ ►. A program that keeps the symbols it draws in one constant can fix a box, if one
turns up, in one place. A character not in this table
has not been tried: draw it once, the way `examples/glyphs/` does, before
building a screen on it.

Only font 3 was tried for the five boxes, so whether fonts 1 and 2 lack them
too is not known. A G2 runs the same firmware and is expected to draw the
same, but that was not checked (unverified).

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, in
the calculator `Prime`, on 2026-09-29, by a one-screen program, HPGLIF. It
cleared the screen with `RECT()`, drew the eight pairs with `TEXTOUT_P` in
font 3, one row each from y 26 to y 180, black, 300 pixels wide, with a word
between the two characters of a pair; drew the font-2 line underneath, at
y 204; and waited for a key
([interface.drain-then-wait](#interface.drain-then-wait)). The person running
it read the screen and sent a screenshot. `examples/glyphs/` draws the same
rows in the same places and fonts. `hpprime lint` flags the five in any
string, as `font-glyph`: a warning, because the program compiles and runs,
labelled `emulator` inside a font-3 `TEXTOUT_P` and `unverified` anywhere
else.

<a name="interface.input-fields"></a>
## What INPUT's field descriptions mean

| | |
|---|---|
| Identifier | `interface.input-fields` |
| Kind | rule |
| Known from | G2 |

`INPUT` returns 1 if accepted and 0 if cancelled. What is measured about its
fields:

| | |
|---|---|
| Field position | `{x%, width%, row}`, as a percentage of the screen |
| The label sits to the left of the field | at `x=5` labels came out clipped to a dot; at `x=22` they fit |
| Field type | `[0]` is real: the number is typed as it is, with no quotes |
| A text field demands quotes | typing `"0.2"` under exam pressure is a tax on every value |
| The variables must already exist, with the right type | |

The quotes detail decides whole interfaces. Given a choice between a form with
blank cells, which needs text fields and therefore quotes, and two drop-downs
plus two numeric fields, the drop-downs win: they say what you know, the
numeric fields say how much, and the label can show the unit.

**Evidence.** Measured on a G2 with firmware 2.4.15515, in an app in daily
use whose form has one drop-down and four fields over two rows.

<a name="interface.input-modal"></a>
## INPUT is modal and builds its labels once

| | |
|---|---|
| Identifier | `interface.input-modal` |
| Kind | rule |
| Known from | unverified |

A label that depends on another field of the same form cannot be refreshed
while the form is open. Offer fixed variants instead, or ask one field at a
time: a one-field `INPUT` can label itself with the unit for that particular
row, and lets somebody correct one value without walking through the other
nine.

**Evidence.** Seen on a G2 with firmware 2.4.15515, with no program kept.

<a name="interface.getkey-position"></a>
## GETKEY returns a position, not a character

| | |
|---|---|
| Identifier | `interface.getkey-position` |
| Kind | rule |
| Known from | G2 |

The code for `[Enter]` is 30, not 13. A code is a position, counted along the
keyboard from the top left, and the same code means different things in
different modes: 42 is `1` in normal mode and `y` in alpha mode.

**Evidence.** Measured on a G2 with firmware 2.4.15515, key by key.

<a name="interface.key-codes"></a>
## The 51 key codes, 0 to 50

| | |
|---|---|
| Identifier | `interface.key-codes` |
| Kind | rule |
| Known from | G2 |

| Where | Codes |
|---|---|
| top block | `Apps` 0, `Symb` 1, ▲ 2, `Help` 3, `Esc` 4 |
| | `Home` 5, `Plot` 6, ◄ 7, ► 8, `View` 9 |
| | `CAS` 10, `Num` 11, ▼ 12, `Menu` 13 |
| keypad, six wide | `Vars` 14, Mem 15, Units 16, `x t θ n` 17, `a b/c` 18, `Del` 19 |
| keypad, six wide | `x^y` 20, `SIN` 21, `COS` 22, `TAN` 23, `LN` 24, `LOG` 25 |
| keypad, five wide | `x²` 26, `+/-` 27, `( )` 28, `Eval` 29, `Enter` 30 |
| | `EEX` 31, `7` 32, `8` 33, `9` 34, `÷` 35 |
| | `ALPHA` 36, `4` 37, `5` 38, `6` 39, `×` 40 |
| | `Shift` 41, `1` 42, `2` 43, `3` 44, `−` 45 |
| | `On` 46, `0` 47, `.` 48, space 49, `+` 50 |

The rows are not all the same width: the two top rows of the white keypad have
six keys and the five below them have five, which is what puts `Del` at 19,
`Enter` at 30 and `+` last at 50. Design to fail quietly: send an unknown code
to the default case, and make that case harmless.

**Evidence.** Measured on a G2 with firmware 2.4.15515, key by key, 51 keys.
To read a code you did not expect, press the key:
`examples/keymap/` prints it.

<a name="interface.soft-labels-not-keys"></a>
## The six labels along the bottom are not keys

| | |
|---|---|
| Identifier | `interface.soft-labels-not-keys` |
| Kind | rule |
| Known from | G2 |

Touching them reports nothing through `GETKEY`: they are touch targets, and
touch arrives through `MOUSE`. What published apps call "soft keys 1..6" are
physical keys -- codes 0, 5, 10, 1, 6, 11, which is `Apps`, `Home`, `CAS`,
`Symb`, `Plot`, `Num`: the top-left 3×2 block, taken column by column. If your
program wants those labels driven from the keyboard as well as by finger, you
pick the physical keys yourself, and that block is what other people picked.

**Evidence.** Measured on a G2 with firmware 2.4.15515: touching the labels
produced no key code. The mapping is read from two published apps.

<a name="interface.draw-then-return"></a>
## A program that draws and returns loses its screen

| | |
|---|---|
| Identifier | `interface.draw-then-return` |
| Kind | rule |
| Known from | G2 |

Run a program from Home, have it draw with `TEXTOUT_P` and then `RETURN`, and
what you are left looking at is Home, with the return value. The drawing does
not survive the program ending, so anything meant to be read has to wait
before it returns. This is the first thing that goes wrong with a diagnostic
program, and it looks like the program did nothing at all.

What you are left with is a framed line in the Home history -- the program's
name and the value it returned -- or, when it was started from the Program
Catalog, a modal pop-up saying the same. It is not a message: it is the return
value, shown the way Home shows the value of anything you type.

Nothing suppresses it, because
[ppl.function-always-answers](ppl.md#ppl.function-always-answers): every
ending produces a number, so every one leaves a line. What you choose is what
the number says, not whether it appears.

**Evidence.** Measured on a G2 with firmware 2.4.15515, with five endings: an
assignment, a loop, an `IF` that does not run, a call, and a bare `RETURN;`.

<a name="interface.drain-then-wait"></a>
## Waiting for a key means draining the buffer first

| | |
|---|---|
| Identifier | `interface.drain-then-wait` |
| Kind | rule |
| Known from | G2 |

```ppl
EXPORT TPAUSE()
BEGIN
  LOCAL zk;
  REPEAT zk := GETKEY; UNTIL zk < 0;    // drain what is pending
  REPEAT zk := GETKEY; UNTIL zk >= 0;   // and only now wait
  RETURN zk;
END;
```

From Python the same principle, with `keyboard()` and `GETKEY()`.

**Evidence.** Measured on a G2 with firmware 2.4.15515: this waits where
`WAIT(-1)` did not, in a program called from another one.

<a name="interface.wait-minus-one"></a>
## WAIT(-1) waits for a key, though one program on a G2 saw it not wait

| | |
|---|---|
| Identifier | `interface.wait-minus-one` |
| Kind | rule |
| Known from | emulator |

In a program run from Home, `WAIT(-1)` waits for a key and answers its code,
as [GETKEY](../commands/io/GETKEY.md) numbers keys: 42 for the key `1`. It
waited straight after the `[Enter]` that started the program, so that key did
not make it return, and it waited after the keyboard had been drained. Only
`1` was pressed during those waits, and `Esc` answered 4 in the program of
[interface.wait-events](#interface.wait-events): whether an `[Enter]`
pressed while it waits ends it the same way was not tried. In two
published apps it is the event loop, answering a number for a key, a list
for a touch and −1 every 60 s. The list is measured, in
[interface.wait-events](#interface.wait-events); the −1 is read from those
apps and not run here (unverified).

One program on a G2 saw it not wait: a results screen flashed past and the
form came straight back. What differed there is not known -- that program was
called from another, just after an `INPUT` -- so it stays unexplained, and
[interface.drain-then-wait](#interface.drain-then-wait) is still the loop
whose behaviour nothing contradicts.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, on
2026-09-24, in the batch program itself, each call timed with `TICKS`: the
first answered `{42,17619}`, 42 after 17.6 seconds, and the second, after a
`GETKEY` loop had drained the keyboard, `{42,13951}`
([results.tsv](../commands/results.tsv)). The person pressing the keys
reported pressing `[Enter]` to start the program, seeing it wait, and then
pressing only `1`. The G2
reading is from a program in daily use, and was not repeated.

<a name="interface.wait-events"></a>
## WAIT(-1) answers a touch as one list per event, and only the click is a tap

| | |
|---|---|
| Identifier | `interface.wait-events` |
| Kind | rule |
| Known from | emulator |

A key comes back from `WAIT(-1)` as a plain number,
[interface.wait-minus-one](#interface.wait-minus-one). Anything on the touch
screen comes back as a list instead, one call per event, and the list's first
element is the event's type:

| Type | Event | What the call answers |
|---|---|---|
| 0 | down | `{0,x,y}` |
| 1 | move | `{1,x,y}` |
| 2 | up | `{2}`: one element, and no position |
| 3 | click | `{3,x,y}`, after the up |

| What was done | What arrived |
|---|---|
| a click, short or held a little longer | down, up, click |
| one notch of the wheel, either way | down, move, up, all at the pointer, and no click |
| a short drag | down, move and up, again and again, and no click |

The two directions of the wheel arrive the same, and no other type appeared,
the longer click included.

The elements are `#` integers, not ordinary numbers: the type arrives as
`#0:64h`, and each coordinate with a width of −16, as `#DD:-16h`.
[B→R](../commands/integer/B→R.md) turns a `#` integer into an ordinary number,
but it was measured on one with no width stated; what it does with these, and
whether `ze(1) == 3` holds without it, was not tried (unverified).

Three rules follow. Treat as a key only a plain number: a one-element list is
an up, and reading its element as a key code makes every click press ▲, code
2, as well. Act on type 3, not type 0: a wheel notch and a drag each begin with
a down, so a program that acts on the down takes every one of them as a tap.
And take the position from the click, since the up carries none. Breaking the
first two has been seen in a program in daily use: each click also acted as
▲, and each wheel notch as a tap. `hpprime lint` warns, as `wait-touch`,
where what `WAIT(-1)` answered is compared with a number in a function that
never asks its `TYPE`. That program did ask it, and then read the
one-element list as a key, which the linter does not see.

What a finger on a G2 sends was not measured: whether it is the same
sequence, and whether a finger that moves a little between down and up still
gets its click, which the drag did not (unverified).

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15,
instance "Prime", on 2026-09-29, operated with a mouse. A one-screen program
looped `ze := WAIT(-1)` and printed each answer with `STRING`, as a number,
or as a list with its `SIZE`, and stopped after two `Esc`, which arrived as
4, plain numbers. The person at the emulator did each action and sent
screenshots. One click answered `{#0:64h,#DD:-16h,#7D:-16h}`, `{#2:64h}`,
`{#3:64h,#DD:-16h,#7D:-16h}`; one wheel notch
`{#0:64h,#103:-16h,#A3:-16h}`, `{#1:64h,#103:-16h,#A3:-16h}`, `{#2:64h}`.
Every position fell inside the 320 × 240 screen: x 221 and 259, y 125 and
163.

<a name="interface.mouse-lists"></a>
## MOUSE returns lists inside lists

| | |
|---|---|
| Identifier | `interface.mouse-lists` |
| Kind | rule |
| Known from | G2 |

`{{x1,y1,x0,y0,type}, …}`. From Python it has to be flattened before it
crosses the bridge, because a list that is not all numbers closes the app
([micropython.md](micropython.md)):

```python
_MOUSE = ('LOCAL zm:=MOUSE; LOCAL zp:=zm(1);'
          ' IFTE(SIZE(zp)==0,{-1,-1,-1},{zp(1),zp(2),zp(5)})')
```

**Evidence.** Measured on a G2 with firmware 2.4.15515, in an app that reads
touch from Python.

<a name="interface.touch-readings"></a>
## A touch reading is not an event

| | |
|---|---|
| Identifier | `interface.touch-readings` |
| Kind | rule |
| Known from | unverified |

Three jobs raw readings leave to you. The coordinates need their sign fixed,
with `(c + 2**63) % 2**64 - 2**63`, which is an unsigned 64-bit value turned
signed; without it you get astronomically large numbers instead of a position
off the edge. `MOUSE` tells you what is happening now and cannot tell a finger
that has just landed from one that has been there half a second, so a layer
keeps the previous reading and derives `down`, a fresh `tap`, and `dx`/`dy`
for a drag. And a tap is reported once, on release: `tap and not down`, true
in exactly one update.

`WAIT(-1)` answers events rather than readings, and its click arrives once,
after the up, with its position:
[interface.wait-events](#interface.wait-events).

**Evidence.** Read from a published Python library's source, not measured
here. Its debounce was arrived at independently by another author, which is
a fair sign it is not optional.

<a name="interface.dialog-touch-twice"></a>
## The touch that closes a dialog arrives again underneath

| | |
|---|---|
| Identifier | `interface.dialog-touch-twice` |
| Kind | rule |
| Known from | G2 |

The Prime's dialogs, `INPUT` and notices, are accepted with an OK button that
falls on top of the soft-key row, in the F6 position. If your finger is still
there when the dialog closes, the same touch arrives at the screen underneath,
as though you had pressed its F6.

A debounce with memory fixes it: count the screen as touched when a dialog
closes, and pass only on the first contact of a new touch, on closing any
dialog and on returning from any screen. Where to put it is a choice:
[patterns.md](../patterns.md#a-touch-debounced-with-memory). It solves two things at once:
the screen is read dozens of times a second while a finger stays down, and the
touch that closes a dialog outlives the dialog.

**Evidence.** Measured on a G2 with firmware 2.4.15515, in an app whose menu
acted on the touch that had just dismissed a notice.

<a name="interface.screen-capacity"></a>
## 20 rows of 40 ordinary characters fit in the small font, with no room to spare

| | |
|---|---|
| Identifier | `interface.screen-capacity` |
| Kind | rule |
| Known from | emulator |

In font 1, twenty rows 12 pixels apart fill the 240-pixel screen, and each
row's ink is about 10 pixels tall, which leaves one or two between rows. A
row of 40 ordinary characters, letters, digits and spaces, takes about 197
of the 320 pixels; 40 digits about 236; 40 `W` do not fit. With soft keys
along the bottom, the 213 pixels above them hold 17 such rows
([interface.geometry](#interface.geometry)). The person who read it said
the rows fit and are very narrow: dense enough to rule a design out, not
to call one comfortable.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, on 2026-10-04, with a program that wrote
twenty rows with `TEXTOUT_P` in font 1 and a width of 320: fourteen of
ordinary text, three of digits, three of `W`, each 40 characters. The widths
and heights above were read from the pixels of a screenshot cropped by hand
at about 2.6 times, so they are good to a pixel or two;
[interface.text-measure](#interface.text-measure) is how a program would
measure them exactly.

The test programs are in [docs/evidence](../evidence/README.md#interface.screen-capacity).

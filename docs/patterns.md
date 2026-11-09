# Patterns: ways apps are built

Nothing on this page is a rule. These are ways that apps which work on the
Prime are built, each with the problem it solves, what it costs, and the facts
it rests on. Pick what fits the app in front of you. One built another way is
not wrong, and a pattern that does not fit is not worth its cost.

What the calculator does is in the topic pages, such as
[ppl.md](topics/ppl.md) and [interface.md](topics/interface.md), and in the
entries. This page is about choices, and where it relies on a fact it links
to it, with its label.

---

## Develop as a program, wrap it as an app at the end

The code is written and tried as a catalogue program, and put into a
`.hpappdir` once it works.

**Solves:** slow iteration. A program is sent and run with nothing around it,
and the `.hpappdir` is a folder that holds the same code
([apps.hpappdir-contents](topics/apps.md#apps.hpappdir-contents), G2).

**Costs:** little, when the app is meant to end up as an app.

**Skip it when** the app's own views and hooks are the point from the start
([apps.hooks](topics/apps.md#apps.hooks), G2).

## The app as a launcher

The engine and the interface stay as catalogue programs, and the app's own
program calls them.

**Solves:** an engine that other apps, or Home, call as well, since what an
app's program exports was seen to be tied to that app
([apps.exports-tied](topics/apps.md#apps.exports-tied), unverified); and data
of hundreds of kilobytes that is not sent again whenever the interface
changes.

**Costs:** several installs instead of one, and in an order, since a program
does not compile until the functions it calls are on the calculator
([ppl.compilation-order](topics/ppl.md#ppl.compilation-order), G2); and names
that differ between the pieces, since exported names share one namespace
([ppl.global-namespace](topics/ppl.md#ppl.global-namespace), G2).

**Skip it when** the app is small and nothing else calls it. One app with one
program is simpler to install and to reason about.

## Logic apart from pixels

What decides the screen -- which row is selected, what text goes in it, what
each key means -- lives in functions that do not draw, and a thin layer does
the drawing:

```
  decides             |  draws
  --------------------|-------------------
  which row is        |  TEXTOUT_P
  selected            |  RECT
  what text goes      |  GETKEY
  in each row         |  DRAWMENU
  what a key means    |
```

**Solves:** testing on the PC. `hpprime run` executes the first column, and
records drawing and input rather than performing them
([tools.md](tools.md#run)), so the decisions can be checked before the
calculator sees them.

**Costs:** structure that a small or mostly visual program may not need.

**Skip it when** the program is mostly drawing, animation or touch, which only
the calculator can judge: test it there.

## One Python file in both places

```
      PC                                   calculator
   ---------                            -----------------
   engine.py   \                       /   LIB (PPL)
                >   data.py (2 faces) <
                                       \   hpprime.eval
                       |
                    app.py      <-- the same file in both places
                       |
                 main / screen         <-- pixels only here
```

`app.py` is identical in the repository and in the app: `hpprime build` copies
it, and `hpprime verify` says when the two have drifted apart. `data.py` is
written twice with the same face, one version over an engine on the PC and one
over the bridge to PPL
([micropython.eval](topics/micropython.md#micropython.eval), G2).

**Solves:** PC tests that say something about the calculator, since the file
that computes is the one that runs there. A test that sends the same record
through both faces also catches a serialised form that drops a field, which a
round trip on the Python side alone can miss when the defaults happen to
match.

**Costs:** the data module written twice, and everything `app.py` imports
limited to what MicroPython has
([micropython.imports](topics/micropython.md#micropython.imports), G2).

**Skip it when** there is no engine on the PC to share, or the app is mostly
interface.

## Update, then draw

The loop reads the inputs, moves the state, and draws the result, rather than
drawing where each input is handled. What such a loop keeps: the touch (`x`,
`y`, the event type, `dx` and `dy` for a drag, whether it is down, whether this
is a fresh tap), the keyboard (the key, and the shift and alpha layers, since
one code means different things in each), and time (milliseconds from
`TICKS`, and the gap since the last update).

**Solves:** a screen that stays consistent when inputs arrive in bursts, and
one place to look when it does not.

**Costs:** a state that has to be kept, where a simple program would just draw.

Time has to come from PPL in a Python app, since MicroPython on the Prime was
seen without a `time` module
([micropython.modules](topics/micropython.md#micropython.modules),
unverified).

## A windowed list

For an app whose data is rows -- records, results, a list of findings -- one
widget can carry most screens: a list with a few visible rows, a top index, a
scrollbar, arrows, touch and digit jump. One layout that worked: a 20 px
header, seven 24 px rows and a help line, in the app area above the soft-key
row ([interface.geometry](topics/interface.md#interface.geometry), G2).

Behaviour the published apps give it: digits jump to a row; selection wraps;
left and right change column when there are several and page when there are
not, as the calculator's own Numeric view does; touching a row selects it and
touching it again enters; `Cancel` and `OK` in soft-key positions 5 and 6;
partial redraw; leaving after a time with no input; `IFERR` around the event
loop; and a two-page soft menu rather than six crowded labels.

**Solves:** many screens from one piece of code, and one set of habits for
the person using it.

**Costs:** writing it once, or installing a library to start from, `CHOOSE_R` or `SkeletonApp`
([libraries.md](topics/libraries.md)). A full event framework with drags, long
presses and many handlers costs more than most apps use.

**Skip it when** the screen is a drawing, a graph or a game.

## A table for values that can be unknown

`INPUT` with several fields has no way to say "I do not know this one", so a
form ends up with an invented `0` for empty, and then a `-1` once `0` turns out
to be a legitimate value. A table has no such problem: an empty cell is empty.
In a table edited by hand, two details came out of use: after an edit the
cursor moves down by itself, since data tends to arrive by column, and
proposed defaults let a chain of linked values be typed without entering the
links.

**Solves:** data entry where some values are not known yet.

**Costs:** a table widget, where `INPUT` comes free
([interface.input-fields](topics/interface.md#interface.input-fields), G2).

**Skip it when** every field always has a value: a form is quicker to write.

## Units shown, not asked for

An app that asks for units at the start lets somebody enter `25` where the
table expects `298`, and the answer comes out computed and wrong. Deriving the
unit from the data and showing it -- in the `INPUT` label, in the help line,
in a column's title -- avoids the question.

**Solves:** a value entered in the wrong unit with nothing to show it.

**Costs:** one fixed set of units, which suits an app built around one table
and not a general calculator.

## A touch debounced with memory

The touch that closes a dialog arrives again at the screen underneath
([interface.dialog-touch-twice](topics/interface.md#interface.dialog-touch-twice),
G2). A debounce with memory is kept in the code that decides, not in
the code that draws: count the screen as touched when a dialog closes, pass
only the first contact of a new touch, and call that from every place that
closes a dialog or returns from a screen.

**Solves:** both the repeated touch and a finger held down being read dozens
of times a second, and it can be tested on the PC like any other decision.

**Costs:** one more piece of state.

## Where these come from

The published apps listed in
[interface.md](topics/interface.md#where-this-comes-from), all running on real
calculators, and one data-table app in daily use on a G2, from which the
launcher, the shared Python file, the windowed list, the table and the units
come. A pattern from one app is one app's experience: what it says about the
calculator is in the facts it links to, and the rest is a choice.

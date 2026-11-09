# Interfaces: what to reach for

Facts about the published libraries, and the judgement about which level a
screen needs. The commands themselves are in
[interface.md](interface.md), and this page does not repeat them.

The Prime's own commands cover more than people expect, and where they stop,
somebody has usually written the missing piece.

## Which level

| What the screen has to do | Comes with the calculator | A library, to install first | Written by you |
|---|---|---|---|
| Ask for one value | `INPUT` with a single field | | |
| Ask for several at once | `INPUT` with a field list, after reading its limits | | |
| Choose one of a handful | `CHOOSE` | | |
| Choose one of many, scrolling | | `CHOOSE_R` | your own list |
| Say something and wait | `MSGBOX`, or `TEXTOUT_P` plus a key wait | | |
| Offer up to six actions | `DRAWMENU` | `LibMenu`, for toggles and pages | |
| A table you move around and edit | | | on the windowed-list pattern |
| A whole app with its own event loop | | `SkeletonApp`, to start from | your own |

Two of those rows are worth expanding before you commit to a design. `INPUT`
is modal and builds its labels once, and a text field makes the user type
quotes: the second is measured, the first was only seen, and both decide layouts
([interface.input-fields](interface.md#interface.input-fields),
[interface.input-modal](interface.md#interface.input-modal)). And a form has no way to say "I do not know this one", which is why some apps
use a table instead ([patterns.md](../patterns.md#a-table-for-values-that-can-be-unknown)).

## Using somebody else's library

A PPL library is a program: you install it the way you install yours, and then
call its exported functions. Three things to know first. Exported names are
global, so a library that exports `draw` or `reset` will collide with yours
([ppl.global-namespace](ppl.md#ppl.global-namespace)); prefix your own, and
check with `hpprime lint A.txt B.txt --set`, which flags exported names that
would clash between files installed together. Order matters, because a program
only sees another's functions if it was compiled afterwards
([ppl.compilation-order](ppl.md#ppl.compilation-order)), so install the
library first. And read it before you trust it: these are one-person projects
with no test suite, and reading the source is also the fastest way to learn
the platform -- the key codes and menu geometry here came from exactly
that.

Where they live: [hpcalc.org](https://www.hpcalc.org/prime/programming/), and
the list below links each one. Most were
announced on the HP Museum forum, which blocks automated access, so a person
has to fetch them.

## When to write your own

When none of them fits, the widget apps most often write is a list with a
window: selection, paging, a scrollbar, digit jump and touch. What apps that
work give it, and what it costs, is in
[patterns.md](../patterns.md#a-windowed-list).

---

<a name="libraries.published"></a>
## What the published libraries give you

| | |
|---|---|
| Identifier | `libraries.published` |
| Kind | rule |
| Known from | unverified |

None of these comes with the calculator. Each is somebody's program, which has
to be installed before anything can call it.

**[CHOOSE_R](https://www.hpcalc.org/details/9104)**, Jacob Wall, version 1.0, 2019 -- `CHOOSE_R(title, items,
cur_sel, del_opt)`. `items` is a list of strings, numbered for you from 1;
`cur_sel` is where the highlight starts; `del_opt` puts a Delete option on the
menu. It answers 0 if cancelled, the index if something was chosen, and the
negative index if Delete was used. Over the built-in `CHOOSE` it adds a
scrolling window with a scrollbar, touch, colours taken from the calculator's
theme, and an automatic exit after a period of inactivity. Its internals are
the clearest worked example of the windowed list.

**[LibMenu](https://www.hpcalc.org/details/7782)**, primer, version 3, 2016 -- the six labels along the bottom, with entries
that toggle and tabs that group them into pages: `reset()`, `draw()`,
`events()`, `deftab(from, to, active)`, `entry(pos, txt, action)`,
`entrytoggle(pos, txt)`, `gettoggle(pos)`, `chgflag(pos)`.

**[SZ_Show_Text](https://www.hpcalc.org/details/8947)**, Sasa, version 1.1, 2018 -- a text display utility, for when
the answer is a paragraph rather than a number.

**[PrimeLibs](https://www.hpcalc.org/details/9544)**, José Felten, version 1.0 alpha -- the only Python toolkit here:
`gui.py` (widget classes), `pointer.py` (touch), `kbd.py` (the keyboard, with
shift and alpha layers), `palette.py` (theme colours), `time.py` (the module
MicroPython does not have, built on `eval('ticks')`), `filebrowser.py`, and
the rest. Every widget derives from `Component`, which carries position and
size and answers `isPressed()` and `isTapped()`, so an app is a loop that
updates and draws a tree of them.

**[SkeletonApp](https://www.hpcalc.org/details/7566)**, Juerg W. Buser -- an app skeleton with a complete event loop:
drags, long press, and a handler per gesture. The soft-menu geometry on these pages
was measured from it. For an app driven by arrows, `Enter` and six buttons,
its full event framework is more than you need: take the loop and leave the
rest.

**Evidence.** Read, not run. The signatures and behaviour above are taken from
each library's own source and header comments; nothing here has been executed
on a calculator, and versions move. The links, and the author of SkeletonApp and
of LibMenu, are what hpcalc.org listed on 2026-11-09.

<a name="libraries.skeletonapp-container"></a>
## SkeletonApp's .hpprgm is not the container the tools read

| | |
|---|---|
| Identifier | `libraries.skeletonapp-container` |
| Kind | rule |
| Known from | unverified |

The file begins `B6 03 00 00` rather than the `7C 61 8A B2` magic
([formats.container](formats.md#formats.container)), so `hpprime read` refuses
it. Take the source from the PDF that ships with it.

**Evidence.** Read from the downloaded file's first bytes. Which tool wrote it
that way, and whether other libraries of the same vintage share the format,
has not been looked into.

<a name="libraries.usb-keyboard"></a>
## A USB keyboard can be read from Python, and nobody here has tried it

| | |
|---|---|
| Identifier | `libraries.usb-keyboard` |
| Kind | rule |
| Known from | unverified |

`PrimeLibs`'s `kbd.py` reads a USB keyboard through `eval('uopen()')` and
`usbrecv`, with control, alt and shift layers. It is not in HP's documentation
either.

**Evidence.** Read from that library's source. One probe app with a USB
keyboard attached would settle whether it works on a G2 with firmware
2.4.15515.

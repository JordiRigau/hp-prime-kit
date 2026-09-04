# Interfaces: what to reach for

The Prime's own commands cover more than people expect, and when they stop
covering it somebody has usually written the missing piece. This page is the
choice: which of the three levels a given screen needs, and what the
published libraries actually give you.

The commands themselves are in [interface.md](interface.md); this page does
not repeat them.

---

## 1. Which level

| What the screen has to do | Reach for |
|---|---|
| Ask for one value | `INPUT` with a single field |
| Ask for several at once | `INPUT` with a field list -- but read its limits first |
| Choose one of a handful | `CHOOSE` |
| Choose one of many, scrolling | **CHOOSE_R** (§3), or your own list |
| Say something and wait | `MSGBOX`, or `TEXTOUT_P` plus a key wait |
| Offer up to six actions | `DRAWMENU`, or **LibMenu** (§3) for toggles and pages |
| A table you move around and edit | your own, on the windowed-list pattern |
| A whole app with its own event loop | your own, or start from **SkeletonApp** (§3) |

Two of those rows are worth expanding before you commit to a design.

**`INPUT` is modal and builds its labels once.** A label that depends on
another field of the same form cannot change while the form is open, and a
text field makes the user type quotes. Both are measured, and both decide
layouts: see [interface.md §4](interface.md#4-input-what-to-know-before-designing-around-it).

**A table beats a form when a value can be unknown.** A form has no way to
say "I do not know this one", so it needs sentinels; an empty cell in a table
is simply empty. [interface.md §8](interface.md#8-a-table-needs-no-sentinels-a-form-does).

## 2. Using somebody else's library

A PPL library is a program. You install it the same way you install yours,
and then call its exported functions.

Three things to know before you do:

- **Exported names are global.** A library that exports `draw` or `reset`
  will collide with yours. Prefix your own, and check with
  `hpprime lint A.txt B.txt --set`, which flags exported names that would
  clash between files installed together.
- **Order matters.** A program only sees another's functions if it was
  compiled afterwards, so install the library first.
- **Read it before you trust it.** These are one-person projects with no test
  suite. Reading the source is also the fastest way to learn the platform --
  the key codes and menu geometry in this kit came from exactly that.

Where they live: [hpcalc.org](https://www.hpcalc.org/prime/). The HP Museum
forum is where most of them were announced, but it blocks automated access,
so a person has to fetch them.

## 3. What the published ones give you

**Read, not run.** The signatures and behaviour below are taken from each
library's own source and header comments. Nothing here has been executed on a
calculator by this kit, and versions move.

### CHOOSE_R -- a better `CHOOSE`

Jacob Wall, version 1.0, 2019.

```ppl
CHOOSE_R(title, items, cur_sel, del_opt)
```

`items` is a list of strings, and it numbers them for you from 1. `cur_sel`
is where the highlight starts, `del_opt` puts a Delete option on the menu.
It answers **0** if cancelled, the **index** if something was chosen, and the
**negative index** if Delete was used.

What it adds over the built-in `CHOOSE`: a scrolling window with a
scrollbar, touch, colours taken from the calculator's theme, and an automatic
exit after a period of inactivity. Its internals are also the clearest
worked example of the windowed list, if you are about to write your own.

### LibMenu -- the soft-key row, with state

Version 3, 2016.

```
reset()                    entry(pos, txt, action)
draw()                     entrytoggle(pos, txt)
events()                   gettoggle(pos)
deftab(from, to, active)   chgflag(pos)
```

The six labels along the bottom, but with entries that toggle and tabs that
group them into pages -- which is what you want past six actions, instead of
cramming six unreadable labels.

### SZ_Show_Text -- text on screen

Sasa, HP Museum forum, version 1.1, 2018. A text display utility: what to use
when the answer is a paragraph rather than a number.

### SkeletonApp -- an app to start from

Andreas Möller. An app skeleton with a complete event loop: drags, long
press, and a handler per gesture. It is where this kit's soft-menu geometry
was measured from.

It is worth knowing that its `.hpprgm` is **not** the container this kit
reads -- the file begins `B6 03 00 00`, not the `7C 61 8A B2` magic -- so
`hpprime read` refuses it. Take the source from the PDF that ships with it.

For an app driven by arrows, `Enter` and six buttons, its full event
framework is more than you need. Take the loop, leave the rest.

## 4. When to write your own

Once, and then four times over. The list with a window -- selection, paging,
a scrollbar, digit jump, touch -- is the same widget as your data screen,
your results screen and your diagnostics screen. Writing it once and using it
four times is the difference between an interface that fits your budget and
one that does not.

The pattern, and the behaviour worth copying from the libraries above, is in
[interface.md §7](interface.md#7-one-widget-for-everything-the-windowed-list).

And whatever you write, keep the split: selection, paging and what each key
means are **pure logic** and can be tested on your PC with `hpprime run`. The
module that touches pixels stays as thin as you can make it, because it is
the only part that cannot be.

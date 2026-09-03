# Measuring key codes

`GETKEY` returns a key **position**, not a character, and the table in
[interface.md](../../docs/reference/interface.md#5-the-keyboard) is part
measured and part read out of other people's apps. This program settles any
of it: press keys one at a time and read the codes off the screen.

```bash
hpprime write examples/keymap/KEYMAP.txt -o KEYMAP.hpprgm
```

Drag `KEYMAP.hpprgm` onto the calculator in the Connectivity Kit window, then
on **Home** type:

```
KEYMAP
```

No parentheses -- Home rejects `KEYMAP()`
([why](../../docs/reference/ppl.md#calling-a-function-from-home)).

It prints one numbered line per key press. `Esc` leaves, and prints its own
code (4) on the way out. If you fill the screen it clears and carries on.

---

## What it has already settled

One run on a G2 mapped the top three rows key by key:

```
        col 0       col 1       col 2   col 3       col 4
row 0   Apps  0     Symb  1     ▲ 2     Help  3     Esc 4
row 1   Home  5     Plot  6     ◄ 7     ► 8         View  9
row 2   CAS  10     Num  11     ▼ 12    Menu 13     14
```

Two things came out of that, both now in
[interface.md](../../docs/reference/interface.md#5-the-keyboard):

- **A code is a position in a grid, five to a row.** Nine keys measured here
  and four read from other people's apps fit the same numbering, and none of
  the thirteen contradicts it.
- **The six on-screen labels are not keys.** Touching them reported nothing
  at all. So the codes two apps use for "soft keys 1..6" -- 0, 5, 10, 1, 6,
  11 -- are physical keys: `Apps`, `Home`, `CAS`, `Symb`, `Plot`, `Num`.

## What is still second-hand

Everything below row 2. `Enter` (30) is measured; backspace, `ON` and the
digits come from reading apps and happen to fit the grid. If you need one of
them for real, this program settles it in one run.

## What to do with an answer

Put it in [interface.md](../../docs/reference/interface.md#5-the-keyboard),
say which calculator and firmware, and mark it measured. That is all the
ceremony there is -- see [CONTRIBUTING.md](../../CONTRIBUTING.md).

A code that does **not** fit the grid is the most interesting result
available here: it would mean the numbering is not what the table above
claims.

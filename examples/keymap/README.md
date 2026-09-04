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

## And then the rest of it

A second run carried the numbering past the top three rows: `Vars` is **14**,
and the codes rise left to right, row by row, to the last key at the bottom
right -- `+`, which is **50**. So the whole keyboard is one grid, 0 to 50.

Laid against a picture of the keyboard, those two numbers fix the whole map:
**the two top rows of the white keypad have six keys and the five below them
have five**, so 14 + 6 + 6 + 5×5 = 51 keys, codes 0 to 50, ending on `+` at
the bottom right.

It is worth knowing how that was got wrong first. Assuming five keys to a row
everywhere also fitted the digits, and looked confirmed -- but it could not
explain why the last code sits at the bottom right instead of starting
another row. The loose end was the clue, and a photograph settled it. A model
that fits the data and leaves something unexplained is not finished.

What is still open is only the keys nobody has pressed: the map covers all
51, and every measured key lands on it, but the ones between the measured
ends were read off the layout rather than measured. Any of them is one run
away with this program.

## What to do with an answer

Put it in [interface.md](../../docs/reference/interface.md#5-the-keyboard),
say which calculator and firmware, and mark it measured. That is all the
ceremony there is -- see [CONTRIBUTING.md](../../CONTRIBUTING.md).

A code that does **not** fit the grid is the most interesting result
available here: it would mean the numbering is not what the table above
claims.

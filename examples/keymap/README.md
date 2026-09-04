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

The whole map it produced is in
[interface.md](../../docs/reference/interface.md#5-the-keyboard): 51 keys,
codes 0 to 50, with the two top rows of the white keypad six keys wide and
the rest five.

Two things that page states and this program is how to check:

- the six labels along the bottom of the screen report **nothing** through
  `GETKEY` -- they are touch targets, and touch arrives through `MOUSE`;
- what other apps call "soft keys 1..6" are physical keys: `Apps`, `Home`,
  `CAS`, `Symb`, `Plot`, `Num`.

## What to do with an answer

Put it in [interface.md](../../docs/reference/interface.md#5-the-keyboard),
say which calculator and firmware, and mark it measured. That is all the
ceremony there is -- see [CONTRIBUTING.md](../../CONTRIBUTING.md).

A code that does **not** fit the grid is the most interesting result
available here: it would mean the numbering is not what the table above
claims.

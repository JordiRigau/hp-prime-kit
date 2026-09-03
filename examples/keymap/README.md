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

## The question currently open

The table lists **soft keys 1..6 as codes 0, 5, 10, 1, 6, 11**, taken from
reading two published apps. But `[Num]` measures **11** as well.

The Prime has no physical F1-F6 keys: the six labels along the bottom of the
screen are touch targets. So when an app says "soft key 6", it means a
physical key it has chosen to drive that position with. The open question is
**which keys those are**.

Those six codes are two columns of three -- `0, 5, 10` and `1, 6, 11` -- which
is the shape of the **top-left block of the keyboard, three rows by two
columns**, if positions are numbered five to a row. That is a reading of the
numbers, not a measurement.

**To settle it**, run KEYMAP and press that block in order: top-left key,
then the one to its right, then the next row down, and so on -- six keys.
Then report the six codes **and the names printed on those keys**. If they
come out as 0, 1, 5, 6, 10, 11 in the order you pressed them, the reading is
right and the sixth of them is `[Num]`.

While you are there, two more that cost nothing:

- **Touch the six on-screen labels.** Nothing should be reported: they are
  touch targets, and touch arrives through `MOUSE`, not `GETKEY`. Confirming
  that is what makes the paragraph above make sense.
- **`Help`**, listed as 3 and inferred, never measured.

## What to do with the answer

Put it in [interface.md](../../docs/reference/interface.md#5-the-keyboard)
with its confidence changed from inferred to measured, and say which
calculator and firmware. That is all the ceremony there is -- see
[CONTRIBUTING.md](../../CONTRIBUTING.md).

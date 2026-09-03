# Measuring the string functions

These two probes are how the string functions came to be covered by the
interpreter, and how the `TEXTOUT_P` width was settled. Both were run on a
G2; the results are below.

They are kept because the same two files answer the questions that are still
open -- `SORT`, and the edges nobody has measured -- with one line changed.
Nothing here is guessed: what the interpreter does not know, it raises on.

```bash
hpprime write examples/strings/SPROBE.txt -o SPROBE.hpprgm
hpprime write examples/strings/TWTEST.txt -o TWTEST.hpprgm
```

Drag both onto the calculator, then on **Home** type `SPROBE`, and after it
`TWTEST` -- no parentheses
([why](../../docs/reference/ppl.md#calling-a-function-from-home)).

## SPROBE: what the functions return

Eleven cases on the string `abcdef`, printed one per line with the result in
brackets so an empty one is visible. What is being pinned down:

| Case | The question |
|---|---|
| `LEFT(s,3)`, `RIGHT(s,3)` | the obvious ones, as a control |
| `MID(s,2,3)` | is the third argument a **length** or an **end position**? |
| `INSTRING(s,"cd")` | 1-based position, and is it 3? |
| `INSTRING(s,"zz")` | what "not found" is: 0, -1, or an error |
| `LEFT(s,0)` | empty string, or an error |
| `LEFT(s,99)`, `MID(s,4,99)` | asking for more than there is: truncated, or an error |

**If it does not compile, that is also an answer** -- it means one of those
commands does not take the arguments used here. Report the line.

## TWTEST: the width argument

`TEXTOUT_P`'s width is what stops text overflowing into the next column, and
its position is documented only for the grob form:

```ppl
TEXTOUT_P(txt, G0, x, y, font, colour [, width])
```

The question was whether the **short** form takes one too. TWTEST draws
three lines of W's:

1. short form, no width -- should run off to the right;
2. short form, a 6th argument of 60 -- clipped at 60 px, or a syntax error;
3. grob form, a 7th argument of 60 -- clipped at 60 px, the known-good one.

If it will not compile, line 2 is the reason, and that settles it.

## What they answered, on a G2

Both were run on 2026-09-03. `s` is `"abcdef"`.

| Case | Result | What it settles |
|---|---|---|
| `LEFT(s,3)` / `RIGHT(s,3)` | `abc` / `def` | the controls |
| `MID(s,2,3)` | `bcd` | the third argument is a **length**, not an end position |
| `MID(s,4,99)` | `def` | it stops at the end instead of failing |
| `INSTRING(s,"cd")` | 3 | 1-based |
| `INSTRING(s,"a")` | 1 | 1-based, confirmed at the first character |
| `INSTRING(s,"zz")` | 0 | not found is **0** |
| `LEFT(s,99)` | `abcdef` | asking for more than there is gives what there is |
| `SIZE(LEFT(s,99))` | 6 | and nothing is padded |
| **`LEFT(s,0)`** | **`abcdef`** | **the trap**: zero does not mean "none", it means "all" |

That last one is why guessing these was never an option. Any hand-written
implementation would return an empty string, and it would have been wrong on
a calculator with no way to tell you.

`TWTEST` answered its question too: the **short form takes a width as its
sixth argument**, clipping identically to the grob form's seventh. The
linter's `textout-width` rule now judges both.

All of it is in `BUILTINS` in `hpkit/interp.py`, with a case each in
`tests/test_interp.py`, so a program using these can now be run on the PC.

## What is still open

- **`SORT`**, on lists and on strings. Nobody has measured it.
- **The edges that were not in the probe**: `RIGHT` past the end,
  `RIGHT(s,0)`, `MID` with two arguments, `MID` starting before 1, a negative
  count, `INSTRING` with an empty second argument. The interpreter raises on
  every one of them rather than extrapolating, and says which measurement is
  missing. Any of them is one run away.

## What happens with the answers

The measured semantics go into `BUILTINS` in `hpkit/interp.py`, each with its
case in `tests/test_interp.py`, and a line of
[tools.md](../../docs/tools.md#run) stops saying they are missing. That is
all the ceremony there is -- see [CONTRIBUTING.md](../../CONTRIBUTING.md).

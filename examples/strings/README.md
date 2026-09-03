# Measuring the string functions

The interpreter covers arithmetic, lists, matrices and control flow, and
deliberately does **not** cover `LEFT`, `RIGHT`, `MID`, `INSTRING` or `SORT`.
Their edge behaviour is not measured here, and a guessed semantics would
return a value where the calculator returns another -- which is exactly the
divergence [`hpprime run`](../../docs/tools.md#run) exists to catch. Anything
not covered raises instead.

That is a real cost: today, a program using `MID` cannot be run on the PC at
all. These two probes are what turns that around.

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

Whether the **short** form takes one is not measured, which is why the
linter's `textout-width` rule judges the grob form only. TWTEST draws three
lines of W's:

1. short form, no width -- should run off to the right;
2. short form, a 6th argument of 60 -- clipped at 60 px, or a syntax error;
3. grob form, a 7th argument of 60 -- clipped at 60 px, the known-good one.

If it will not compile, line 2 is the reason, and that settles it.

## What happens with the answers

The measured semantics go into `BUILTINS` in `hpkit/interp.py`, each with its
case in `tests/test_interp.py`, and the coverage table in
[tools.md](../../docs/tools.md#run) stops saying they are missing. If the
short form does take a width, the linter rule widens to cover it.

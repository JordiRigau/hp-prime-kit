# TICKS

Milliseconds since the calculator started.

| | |
|---|---|
| Syntax | `TICKS` → number |
| Group | more |
| Runs on the PC | no |

## Examples

| Call | Result | Known from |
|---|---|---|
| `TICKS` | `120274` | [emulator](../results.tsv) |

## Behaviour

**Written without parentheses in PPL**, `zt := TICKS;` (G2), as any call with no
arguments can be,
[ppl.call-no-parentheses](../../topics/ppl.md#ppl.call-no-parentheses). Typed on
Home with them, `TICKS()` answered *syntax error* with `Entry` at 0 (G2 and
emulator) and at 1, and a number at 2, the RPN stack (emulator),
[ppl.home-no-parentheses](../../topics/ppl.md#ppl.home-no-parentheses).
From Python, across the bridge, `TICKS`, `TICKS()`, `ticks` and `ticks()`
all answer the same number, as a `float` (emulator),
[micropython.eval-parentheses](../../topics/micropython.md#micropython.eval-parentheses).

The number above is the one that batch happened to see, about two minutes
after that emulator started (emulator). It is only useful as a difference:
read it before and after, and subtract. What it does when the calculator has
been on for a long time, and whether it wraps, has not been measured
(unverified).

It is the whole reason MicroPython on the Prime can time anything at all,
since that has no `time` module (unverified),
[micropython.modules](../../topics/micropython.md#micropython.modules).

The interpreter does not implement it, so `hpprime run` cannot check a program
that uses it (unverified).

## Related

[TEVAL](TEVAL.md) · [ppl.speed-anchor](../../topics/ppl.md#ppl.speed-anchor)

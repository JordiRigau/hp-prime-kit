# FREEZE

Keeps what is on the screen until a key is pressed.

| | |
|---|---|
| Syntax | `FREEZE` → number |
| Group | drawing |
| Runs on the PC | no |

## Examples

| Call | Result | Known from |
|---|---|---|
| `FREEZE` | `1` | [emulator](../results.tsv) |

## Behaviour

**Written without parentheses**, `FREEZE;` (emulator), as a call with no
arguments can be in source,
[ppl.call-no-parentheses](../../topics/ppl.md#ppl.call-no-parentheses).

It answered 1 in a batch and did not stop the program (emulator), so whatever
it froze was released without anybody pressing a key. What it does in a
program that has just drawn something, which is what it is for, has not been
measured here (unverified): it is the documented way to stop the screen being
wiped when the program ends, and that case needs a person watching.

The problem it solves is measured, though, and it is a real one: a program
that draws and then returns leaves you looking at Home, with the drawing gone
(G2),
[interface.draw-then-return](../../topics/interface.md#interface.draw-then-return).
The other measured answer to it is to wait for a key yourself
([interface.drain-then-wait](../../topics/interface.md#interface.drain-then-wait)).

The interpreter does not implement it, so `hpprime run` cannot check a program
that uses it (unverified).

## Related

[interface.draw-then-return](../../topics/interface.md#interface.draw-then-return) ·
[GETKEY](../io/GETKEY.md)

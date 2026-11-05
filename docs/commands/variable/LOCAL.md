# LOCAL

Declares variables that last until the end of their block.

| | |
|---|---|
| Syntax | `LOCAL Var1[:=Val1, Var2:=Val2, ... Var8:=Val8];` |
| Group | variable |
| Runs on the PC | yes |

## Examples

| Call | Result | Known from |
|---|---|---|
| `LOCAL za, zb; za := 2; zb := 3; RETURN za * zb;` | `6` | [emulator](../results.tsv) |
| `LOCAL z := 7; RETURN z;` | `7` | [emulator](../results.tsv) |
| `LOCAL za := 2, zb := 3; RETURN za + zb;` | `5` | [emulator](../results.tsv) |
| `LOCAL z; RETURN z;` | `0` | [emulator](../results.tsv) |

## Behaviour

A `LOCAL` can go after other statements, not only at the top of the `BEGIN` (G2):
[ppl.locals-at-top](../../topics/ppl.md#ppl.locals-at-top). It lasts until the end
of the block that declares it, and used after that it does not compile (G2):
[ppl.local-block-scope](../../topics/ppl.md#ppl.local-block-scope).

One `LOCAL` statement holds at most 8 variables, and past that the
compiler answers *syntax error* on that line without saying why (G2):
[ppl.local-limit](../../topics/ppl.md#ppl.local-limit). Several `LOCAL`
statements in a row do work, so a longer list is split across several.

A local declared and never assigned starts at 0, which is the fourth example
(emulator). A `LOCAL` can also give initial values: one on its own and two on
one line both compile and keep their values, the second and third examples
(emulator), and so do three (emulator), which is
[ppl.locals-initialised-one-line](../../topics/ppl.md#ppl.locals-initialised-one-line).
HP's syntax allows up to eight (HP help). Exported globals can too, up to 8 in
one statement (G2),
[ppl.export-initialised](../../topics/ppl.md#ppl.export-initialised).

Prefixed names (`zi`, `zs`, `za`) cost nothing and keep a local away from the
calculator's own variables. `i` and `e` work as local names (emulator):
[ppl.i-e-as-locals](../../topics/ppl.md#ppl.i-e-as-locals).

## Related

[EXPORT](EXPORT.md) · [BEGIN](../block/BEGIN.md) ·
[ppl.local-limit](../../topics/ppl.md#ppl.local-limit)

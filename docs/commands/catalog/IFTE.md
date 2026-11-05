# IFTE

Answers one of two values, depending on a test.

| | |
|---|---|
| Syntax | `IFTE(Expr, TrueClause, FalseClause)` |
| Group | catalog |
| Runs on the PC | yes |

## Examples

| Call | Result | Known from |
|---|---|---|
| `EXPR("IFTE(1<2,10,20)")` | `10` | [emulator](../results.tsv) |

## Behaviour

`IFTE(1<2,10,20)` answers 10 (emulator): the test holds, so the second
argument is the answer. It is a plain real, type 0,
[ppl.type-codes](../../topics/ppl.md#ppl.type-codes).

**It is an expression, where `IF` is a statement** (emulator). This can sit
inside a larger formula and give it a value, which a branch cannot do. That
is the reason to reach for it rather than for [IF](../branch/IF.md).

**It is the two-case form of [PIECEWISE](PIECEWISE.md)** (emulator), which
takes up to eight test-and-value pairs and answers the first that holds.
Where a program has exactly one condition, this is the shorter spelling of
the same thing.

**Only the clause that wins is evaluated** (emulator): the other is skipped
whole, calls and all. So `IFTE(SIZE(L) == 0, 0, L(1))` is safe with an empty
list, and a clause that is slow or changes something costs nothing when it
loses. The measurement is in
[ppl.short-circuit](../../topics/ppl.md#ppl.short-circuit), which says the
same of `AND` and `OR`.

## Related

[PIECEWISE](PIECEWISE.md) · [IF](../branch/IF.md) ·
[ppl.type-codes](../../topics/ppl.md#ppl.type-codes) ·
[ppl.short-circuit](../../topics/ppl.md#ppl.short-circuit)

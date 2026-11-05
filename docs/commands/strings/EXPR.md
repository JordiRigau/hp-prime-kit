# EXPR

Evaluates a string as if it had been typed.

| | |
|---|---|
| Syntax | `EXPR(String)` |
| Group | strings |
| Runs on the PC | yes |

## Examples

| Call | Result | Known from |
|---|---|---|
| `EXPR("2+3")` | `5` | [emulator](../results.tsv) |
| `EXPR("")` | *error* | [G2](../../topics/ppl.md#ppl.expr-empty) |

## Behaviour

An empty string is an error, so anything that comes out of a field is checked
with `SIZE(s) > 0` before it is evaluated (G2):
[ppl.expr-empty](../../topics/ppl.md#ppl.expr-empty). `hpprime lint` warns
about an `EXPR` with no such guard nearby, as `expr-empty`.

It is also how a name is resolved at run time: `EXPR("NAME")` gives the
variable whose name was built on the fly. That is worth doing once when a
program loads and never once per element (G2),
[ppl.expr-dynamic-access](../../topics/ppl.md#ppl.expr-dynamic-access).

**A string the calculator will not accept fails here, and the failure is
trappable** (emulator). Both an empty string and a call the compiler itself
refuses come back as errors caught by [IFERR](../branch/IFERR.md), with the
program carrying on afterwards.

That is what makes this the safe way to try a form nobody has run yet
(emulator). Written straight into the source, a call the compiler cannot read
has the whole program refused and takes every good line with it; written as a
string, it is one row's error and the rest still answer. It is also why the
refusals recorded in [NTHROOT](../catalog/NTHROOT.md),
[NEG](../catalog/NEG.md) and [INVERSE](../catalog/INVERSE.md) could be
measured at all, and it pairs with
[ppl.check-last-error](../../topics/ppl.md#ppl.check-last-error), which says a
refused program names one bad line at a time.

## Related

[STRING](STRING.md) · [IFERR](../branch/IFERR.md) ·
[ppl.expr-empty](../../topics/ppl.md#ppl.expr-empty)

# STRING

Turns a value into text.

| | |
|---|---|
| Syntax | `STRING(Expression)` → string |
| Syntax | `STRING(Expression, [Mode], [Precision], [Separator])` → string |
| Group | strings |
| Runs on the PC | yes |

## Examples

| Call | Result | Known from |
|---|---|---|
| `STRING(2+3)` | `"5"` | [emulator](../results.tsv) |
| `DIM(STRING("abc"))` | `5` | [emulator](../results.tsv) |
| `STRING({1,2})` | `"{1,2}"` | [emulator](../results.tsv) |

## Behaviour

**A string comes back quoted**: `STRING("abc")` answers `"abc"` with the two
quotes inside the result, so it is not the identity on text (emulator). It
took two batches to know that honestly. The first stored `"\"abc\""` for
`STRING("abc")`, which looks like proof and is not: the harness brings every
answer back by applying `STRING` to it, so a call that already answered text
was measured with two of them. That reading was withdrawn. The clean probe
is the one above -- `DIM(STRING("abc"))` counts the characters without
bringing the text back through `STRING` again -- and 5 rather than 3 says
the quotes are there.

A list comes back in PPL's own braces, `{1,2}` (emulator). The interpreter
wrote Python's `[1.0, 2.0]` there until the same comparison caught it.

A number that is not whole comes back with **twelve significant digits**:
`STRING(1/3)` answers `"0.333333333333"` (emulator). That call is not an
example above because the interpreter formats decimals its own way and
changing that would change concatenation too; the measurement is in
[results.tsv](../results.tsv) and the change is a decision of its own.
Source is a different matter: there the separator is always a dot, whatever
the calculator displays (unverified),
[ppl.decimal-point](../../topics/ppl.md#ppl.decimal-point).

HP's help gives three optional arguments -- a mode, a precision and a
separator -- and no example of any of them (HP help). Nothing here has run
them, so the entry does not say what they do.

**The text follows Home's number format** (emulator). With
[HFormat](../home-settings/HFormat.md) at 1 and
[HDigits](../home-settings/HDigits.md) at 2, `STRING(1/3)` answered `"0.33"`;
at the reset settings it is `"0.333333333333"`. A program that builds text
from a number, or compares one, depends on two settings it may never have
set. The interpreter on the PC writes numbers one way only (unverified: that
is the interpreter, not a calculator).

## Related

[EXPR](EXPR.md) · [DIM](DIM.md) ·
[ppl.decimal-point](../../topics/ppl.md#ppl.decimal-point)

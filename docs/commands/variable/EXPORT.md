# EXPORT

Makes a function or a variable visible from Home and from other programs.

| | |
|---|---|
| Syntax | `EXPORT FunctionName(Parameters)` |
| Syntax | `EXPORT Var1[:=Val1, Var2:=Val2, ...];` |
| Group | variable |
| Runs on the PC | no |

## Examples

| Call | Result | Known from |
|---|---|---|
| `EXPORT AREA(zr);` | *no value* | HP help |

## Behaviour

A declaration rather than a call, which is why there is nothing to record
(HP help). Without it, a function is private to its own file.

Exported names share one namespace with Home, so two programs exporting
`AREA` collide, and so does a program exporting a name an app already uses
(G2): [ppl.global-namespace](../../topics/ppl.md#ppl.global-namespace).
Prefixing them is the habit that avoids it, and `hpprime lint --set` flags
names that would clash between files installed together.

One `EXPORT` statement holds up to 8 variables, with initial values or with none,
and 9 do not compile (G2):
[ppl.export-initialised](../../topics/ppl.md#ppl.export-initialised). Locals have
their own limit ([LOCAL](LOCAL.md)).

One of Home's variables cannot be exported: `EXPORT Z := 1;` does not compile,
and neither does `EXPORT Z;` (G2). A function called `F` compiles, but typed on
Home `F` answers the variable (G2),
[ppl.export-home-variable](../../topics/ppl.md#ppl.export-home-variable).

A program only sees another's functions if it was compiled afterwards (G2):
[ppl.compilation-order](../../topics/ppl.md#ppl.compilation-order). Install
the data first, then the engine, then the app.

On Home, type an exported function with no arguments without parentheses (G2):
[ppl.home-no-parentheses](../../topics/ppl.md#ppl.home-no-parentheses). In source
they are optional (G2):
[ppl.call-no-parentheses](../../topics/ppl.md#ppl.call-no-parentheses).

`hpprime run` reads `EXPORT` at the top of a program -- that is how every
example in this documentation is run -- but not as a statement inside a body,
which is what the field above is saying no to (unverified).

## Related

[LOCAL](LOCAL.md) · [BEGIN](../block/BEGIN.md) ·
[ppl.global-namespace](../../topics/ppl.md#ppl.global-namespace)

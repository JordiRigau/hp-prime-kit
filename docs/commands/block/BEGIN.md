# BEGIN

Opens a function's body, and `END;` closes it.

| | |
|---|---|
| Syntax | `BEGIN commands; END;` |
| Group | block |
| Runs on the PC | no |

## Examples

| Call | Result | Known from |
|---|---|---|
| `BEGIN commands; END;` | *no value* | HP help |

## Behaviour

Every function has one: the `BEGIN` after its name opens its body, and the
matching `END;` closes both (HP help). There is nothing to record for it on
its own, because it is the shape of a program rather than a call that
answers.

**A `BEGIN` block inside a body does not compile** (emulator). `BEGIN` opens
a function's body and nothing else: it is not a way to group statements, and
there is no block statement in PPL.

That took two measurements to pin down. On 2026-09-12 a batch of 61 calls
was refused at its third line, which held
`LOCAL z; z := 0; BEGIN z := 5; END; RETURN z;` -- an example this entry
stated at the time, written from what the interpreter accepted rather than
from the calculator. The line was dropped and the batch ran. Then a program
written by hand for the question, with that construct alone in a function,
was refused again at exactly that line (emulator), which is what separates
"the nested block is illegal" from "something else on that line was wrong".

The interpreter accepted it until then, which is how the wrong example came
to be written, and it refuses it now (emulator).

A `LOCAL` does not have to come first in the `BEGIN`: after other statements it
compiles and works (G2),
[ppl.locals-at-top](../../topics/ppl.md#ppl.locals-at-top). How many
variables one `LOCAL` may hold is
[ppl.local-limit](../../topics/ppl.md#ppl.local-limit).

The `END` carries a semicolon (unverified):
[ppl.end-semicolon](../../topics/ppl.md#ppl.end-semicolon). There is no
`ENDIF`, `ENDFOR` or `ENDWHILE` to close anything else with (G2),
[ppl.no-end-keywords](../../topics/ppl.md#ppl.no-end-keywords).

## Related

[RETURN](RETURN.md) · [LOCAL](../variable/LOCAL.md) ·
[ppl.locals-at-top](../../topics/ppl.md#ppl.locals-at-top)

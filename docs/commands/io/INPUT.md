# INPUT

Asks a person for one or more values, in a modal form.

| | |
|---|---|
| Syntax | `INPUT(var, ["title"], ["label"], ["help"], [reset_value], [initial_value])` |
| Syntax | `INPUT({fields}, "title", {labels}, {help})` |
| Group | io |
| Runs on the PC | yes |

## Examples

| Call | Result | Known from |
|---|---|---|
| `INPUT(V,"title","label","help")` | *no value* | HP help |

## Behaviour

There is nothing to record: it waits for a person, and a batch on the
emulator has nobody to answer it. What it gives back when somebody does is
**1 if accepted and 0 if cancelled** (G2),
[interface.input-fields](../../topics/interface.md#interface.input-fields),
which also holds what the field descriptions mean: the position is
`{x%, width%, row}` as a percentage of the screen, a label at `x=5` came out
clipped to a dot while `x=22` fitted, and `[0]` is a real field whose number
is typed without quotes while a text field demands them.

**It is modal and builds its labels once** (unverified),
[interface.input-modal](../../topics/interface.md#interface.input-modal): a
label that depends on another field of the same form cannot change while the
form is open. Asking one value at a time is the measured way round that, and
it also lets somebody correct one value without walking through the other
nine.

The variables have to exist already, with the right type (G2).

`hpprime run` records the call rather than drawing it and answers a neutral
value, so a calculation runs end to end on the PC with no interface, and what
the form looked like is not something it can check (unverified: that is the
interpreter, not the calculator)
([interface.md](../../topics/interface.md#what-the-design-of-a-screen-comes-down-to)).

## Related

[CHOOSE](CHOOSE.md) · [MSGBOX](MSGBOX.md) ·
[interface.input-fields](../../topics/interface.md#interface.input-fields)

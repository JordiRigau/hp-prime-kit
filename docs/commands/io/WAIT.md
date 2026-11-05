# WAIT

Pauses for a number of seconds, or until a key is pressed.

| | |
|---|---|
| Syntax | `WAIT(n)` |
| Group | io |
| Runs on the PC | yes |

## Examples

| Call | Result | Known from |
|---|---|---|
| `WAIT(1)` | *no value* | HP help |

## Behaviour

There is nothing to record: what it produces is a pause, and a batch that ran
it would only be slower (HP help). `hpprime run` answers 30 for this call,
which is the interpreter's own stand-in for a keypress and **not** evidence
about the calculator (unverified): the entry states no result rather than
that number.

**`WAIT(-1)` waits for a key and answers its code** (emulator): in a
program run from Home it waited twice, straight after the `[Enter]` that
started it and after the keyboard had been drained, and answered 42, the key
`1`, the only key tried,
[interface.wait-minus-one](../../topics/interface.md#interface.wait-minus-one).
One program on a G2 saw it not wait at all, and why is not known
(unverified).

**A touch answers a list, one event per call** (emulator): down `{0,x,y}`,
move `{1,x,y}`, up `{2}` with no position, and click `{3,x,y}` after the up,
each element a `#` integer. A wheel notch and a drag bring a down and no
click, so a program acts on type 3, and a one-element list is an up, not a
key,
[interface.wait-events](../../topics/interface.md#interface.wait-events).
What a finger on a G2 sends was not measured (unverified).

What does work, measured, is to drain and then wait with
[GETKEY](GETKEY.md) (G2),
[interface.drain-then-wait](../../topics/interface.md#interface.drain-then-wait).
`WAIT(-1)` would use less battery and deliver touches in the same place;
the G2 reading is the reason to check it in your own program.

## Related

[GETKEY](GETKEY.md) · [FREEZE](../drawing/FREEZE.md) ·
[interface.wait-minus-one](../../topics/interface.md#interface.wait-minus-one) ·
[interface.wait-events](../../topics/interface.md#interface.wait-events)

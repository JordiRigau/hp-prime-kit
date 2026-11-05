# GETKEY

The key waiting to be read, or −1 when there is none.

| | |
|---|---|
| Syntax | `GETKEY` → number |
| Group | io |
| Runs on the PC | no |

## Examples

| Call | Result | Known from |
|---|---|---|
| `GETKEY` | `-1` | [emulator](../results.tsv) |

## Behaviour

**In PPL it works with and without parentheses**: `zk := GETKEY;` and
`zk := GETKEY();` compile and answer the same (G2),
[ppl.getkey-no-parentheses](../../topics/ppl.md#ppl.getkey-no-parentheses).
From Python, across the bridge, the examples here write `GETKEY()`.

It does not wait. With nothing pending it answers −1 straight away
(emulator), which is what makes the measured loop possible: read until it
answers −1 to drain what is pending, then read until it answers something
else (G2),
[interface.drain-then-wait](../../topics/interface.md#interface.drain-then-wait).

What it answers is a **position**, not a character: `[Enter]` is 30, and the
same code means different things in different modes (G2),
[interface.getkey-position](../../topics/interface.md#interface.getkey-position).
The 51 codes are in
[interface.key-codes](../../topics/interface.md#interface.key-codes).

The negative comes back written with the calculator's own minus sign, U+2212
(emulator), [ppl.minus-sign](../../topics/ppl.md#ppl.minus-sign).

The interpreter records it rather than reading a keyboard, so `hpprime run`
cannot check what a program does with a real key (unverified).

## Related

[ISKEYDOWN](ISKEYDOWN.md) · [MOUSE](MOUSE.md) ·
[interface.key-codes](../../topics/interface.md#interface.key-codes)

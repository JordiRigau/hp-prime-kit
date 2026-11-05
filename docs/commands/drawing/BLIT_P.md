# BLIT_P

Copies one grob into another, in pixels.

| | |
|---|---|
| Syntax | `BLIT_P(target, source)` |
| Syntax | `BLIT_P(target, x, y, source [, ...])` |
| Group | drawing |
| Runs on the PC | no |

## Examples

| Call | Result | Known from |
|---|---|---|
| `DIMGROB_P(G1,10,10,0); DIMGROB_P(G2,10,10,0); RETURN BLIT_P(G2,G1);` | `1` | [emulator](../results.tsv) |

## Behaviour

It answers 1, like the rest of the drawing commands (emulator). The two-grob
form was the one run, and which argument is the target is not something the
answer can show: it is the first, by HP's syntax (HP help), and reading a
pixel back from each afterwards is the probe that would confirm it
(unverified).

**This is the second half of drawing without flicker**: build the picture in
a grob of your own with [DIMGROB_P](DIMGROB_P.md), then copy it to `G0`, the
screen, in one go (unverified),
[interface.offscreen-grob](../../topics/interface.md#interface.offscreen-grob).
Painting straight onto `G0` shows the work row by row.

The interpreter does not implement it, so `hpprime run` cannot check a program
that uses it (unverified).

## Related

[DIMGROB_P](DIMGROB_P.md) · [SUBGROB_P](SUBGROB_P.md) ·
[interface.offscreen-grob](../../topics/interface.md#interface.offscreen-grob)

# DIMGROB_P

Creates an off-screen picture of a given size, in pixels.

| | |
|---|---|
| Syntax | `DIMGROB_P(grob, width, height, colour)` |
| Group | drawing |
| Runs on the PC | no |

## Examples

| Call | Result | Known from |
|---|---|---|
| `DIMGROB_P(G1,100,50,0)` | `1` | [emulator](../results.tsv) |

## Behaviour

It answers 1, which is an acknowledgement rather than a value: eleven of the
drawing commands measured in the same batch answer the same 1 (emulator).
What it leaves behind is the grob.

**The size is in pixels**, and it is the size you get back: a grob made 100
by 50 measures 100 through [GROBW_P](GROBW_P.md) and 50 through
[GROBH_P](GROBH_P.md) (emulator), where those two entries hold the rows that
measured it. The forms without `_P` answer 10 and 5 for
that same grob, which is the open question
[GROBW](GROBW.md) holds.

The colour fills it: a grob created with 0 reads back `#0h` at its pixels,
and one created with `RGB(255,0,0)` reads back red
([GETPIX_P](GETPIX_P.md), [PIXOFF_P](PIXOFF_P.md)) (emulator).

`G0` is the screen and `G1` to `G9` are yours (unverified),
[interface.offscreen-grob](../../topics/interface.md#interface.offscreen-grob).
Drawing into one of your own and copying it across with
[BLIT_P](BLIT_P.md) is the measured way to redraw without flicker.

The interpreter does not implement it, so `hpprime run` cannot check a program
that uses it (unverified).

## Related

[GROBW_P](GROBW_P.md) · [GROBH_P](GROBH_P.md) · [BLIT_P](BLIT_P.md) ·
[GETPIX_P](GETPIX_P.md)

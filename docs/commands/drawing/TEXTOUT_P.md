# TEXTOUT_P

Draws text, and answers the x it finished at.

| | |
|---|---|
| Syntax | `TEXTOUT_P(text, x, y, font, colour [, width])` |
| Syntax | `TEXTOUT_P(text, grob, x, y, font, colour [, width])` |
| Group | drawing |
| Runs on the PC | no |

## Examples

| Call | Result | Known from |
|---|---|---|
| `DIMGROB_P(G9,512,22,0); RETURN TEXTOUT_P("abc",G9,0,0,2);` | `19` | [emulator](../results.tsv) |

## Behaviour

**It answers where it stopped.** Three characters in font 2, starting at x 0,
end at x 19 (emulator), so the string is 19 pixels wide. That return value is
the only way to measure text on this calculator, and drawing into an
off-screen grob is how you measure without anybody seeing it
([interface.text-measure](../../topics/interface.md#interface.text-measure)).

**Pass the width.** Without the last argument a long string is painted over
the next column and keeps going off the screen, and nothing raises an error
(G2), [interface.textout-width](../../topics/interface.md#interface.textout-width).
`hpprime lint` catches the missing argument in both forms, as
`textout-width`.

**Some characters come out as an empty box.** In font 3, ◄ U+25C4 is drawn
as an empty box while its pair ► is drawn, and so are ◂ ▸ and ⯇ ⯈; ◀ ▶ and
← → are drawn, and nothing raises an error (emulator),
[interface.font-glyphs](../../topics/interface.md#interface.font-glyphs).
`hpprime lint` flags those five, as `font-glyph`.

Fonts run 1 small, 2 normal, 3 large, up to 7 (HP help). The colour is an
integer of the kind [RGB](RGB.md) answers (emulator).

The interpreter records the call rather than drawing it, and returns a
neutral value (unverified), so `hpprime run` can run a program with an
interface without one and cannot check what it looked like
([interface.md](../../topics/interface.md#what-the-design-of-a-screen-comes-down-to)).

## Related

[RGB](RGB.md) · [GROBW_P](GROBW_P.md) ·
[interface.textout-width](../../topics/interface.md#interface.textout-width) ·
[interface.font-glyphs](../../topics/interface.md#interface.font-glyphs)

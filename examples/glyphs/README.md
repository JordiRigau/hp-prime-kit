# Measuring which symbols the font has

`TEXTOUT_P` draws an empty box for a character its font has no glyph for, and
raises no error. This program draws eight left/right pairs of arrows and
triangles in font 3, and a reference line in font 2, and waits for a key so
the screen can be read.

```bash
hpprime write examples/glyphs/GLYPHS.txt -o GLYPHS.hpprgm
```

Drag `GLYPHS.hpprgm` onto the calculator in the Connectivity Kit window, or
put it on the emulator with `hpprime install GLYPHS.hpprgm --restart`, then on
**Home** type:

```
GLYPHS
```

No parentheses: Home rejects `GLYPHS()`
([why](../../docs/topics/ppl.md#ppl.home-no-parentheses)).

Any key leaves, and the program returns that key's code.

`hpprime lint` warns about this file, as `font-glyph`: it draws the
characters that come out as a box on purpose.

---

What it showed on the Virtual Calculator is in
[interface.md](../../docs/topics/interface.md#interface.font-glyphs): five of
the sixteen characters come out as an empty box, and ◄ is one of them while
its pair ► is not.

To try other characters, change the two lists `zl` and `zr`: one pair per
row, and eight rows fit above the reference line.

## What to do with an answer

Put it in [interface.md](../../docs/topics/interface.md#interface.font-glyphs),
say which calculator and firmware, which font, and whether you read it off a
G2 or the emulator. A character from a G2 is worth most: nothing there has
been checked on one. See [CONTRIBUTING.md](../../CONTRIBUTING.md).

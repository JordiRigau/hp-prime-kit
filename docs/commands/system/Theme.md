# Theme

The display theme, as a list of two integers.

| | |
|---|---|
| Syntax | `Theme` → list |
| Syntax | `Theme:=value` |
| Group | system |
| Runs on the PC | no |

## Examples

| Call | Result | Known from |
|---|---|---|
| `EXPR("Theme")` | `{#1:64h,#5:64h}` | [emulator](../results.tsv) |
| `LOCAL o; o := EXPR("Theme"); EXPR("Theme:=" + STRING(o)); RETURN EXPR("Theme");` | `{#1:64h,#5:64h}` | [emulator](../results.tsv) |

## Behaviour

**It is a list of two based integers** (emulator): `{#1:64h,#5:64h}` on a
reset calculator, and `{#2:64h,#5:64h}` with the colour theme set to dark by
hand (emulator). So the first number is the theme, 2 for dark; that 1 is the
light one is taken from the reset calculator rather than seen (unverified),
and what the second selects was not measured (unverified).

**A program can assign it** (emulator): given its own value back, it was
accepted and read back the same.

**In the dark theme `RECT()` clears to near-black** (emulator), so black
text on it can hardly be read, while black on a rectangle the program fills
white reads fine:
[interface.two-themes](../../topics/interface.md#interface.two-themes).

The interpreter does not implement it, so `hpprime run` cannot check a program
that uses it (unverified).

## Related

[interface.two-themes](../../topics/interface.md#interface.two-themes) · [Language](Language.md)

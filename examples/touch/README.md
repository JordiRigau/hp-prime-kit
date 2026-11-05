# Measuring touch

A program hears a finger in two ways: as events, which
[WAIT(-1)](../../docs/commands/io/WAIT.md) answers one at a time, and as
readings, which [MOUSE](../../docs/commands/io/MOUSE.md) answers whenever it
is asked. This file holds one program for each, and each prints what it
receives.

```bash
hpprime write examples/touch/TOUCH.txt -o TOUCH.hpprgm
```

Drag `TOUCH.hpprgm` onto the calculator in the Connectivity Kit window, then
on **Home** type one of:

```
TOUCHEV
TOUCHMS
```

No parentheses: Home rejects `TOUCHEV()`
([why](../../docs/topics/ppl.md#ppl.home-no-parentheses)).

| | Prints | Leaves with |
|---|---|---|
| `TOUCHEV` | one line per event from `WAIT(-1)`. A list is shown as ordinary numbers, then whether its first element equals its own conversion (`eq 1` or `eq 0`), then the list as the calculator prints it. A key is shown with its `TYPE` | `Esc` twice |
| `TOUCHMS` | one line each time `MOUSE` answers something different, with the milliseconds since the last change | `Esc` |

In both, `Enter` clears the screen, so each thing you try can have a screen
of its own to photograph. A full screen clears and carries on.

It cannot run on the PC: `hpprime run` does not read the `→` in `B→R`, and
no key would end the loops there.

## What it settles

| Fact | What to try | What settles it |
|---|---|---|
| [interface.wait-events](../../docs/topics/interface.md#interface.wait-events) | `TOUCHEV`, with a finger on a G2: a tap, a tap with a little movement, a drag | whether a finger sends the sequences a mouse sent on the emulator, and whether a tap that moves a little still ends in type 3 |
| the same | `TOUCHEV`, anywhere | whether `B→R` turns the `:-16` coordinates into the numbers, and whether `eq` comes out 1 |
| [interface.wait-minus-one](../../docs/topics/interface.md#interface.wait-minus-one) | `TOUCHEV`, then touch nothing for a minute | whether a −1 arrives every 60 s |
| [interface.touch-readings](../../docs/topics/interface.md#interface.touch-readings) | `TOUCHMS`: a finger held still, then lifted; a drag; a drag off the edge | whether a held finger keeps answering the same reading, what the fifth element does, and what a position off the screen looks like |

## What to do with an answer

Put it in the fact it settles, say which calculator and firmware, and change
its label: see [CONTRIBUTING.md](../../CONTRIBUTING.md).

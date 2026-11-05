# 3. Asking for data and drawing

Your program works, and now it has to talk to somebody. The Prime gives you a
touch screen, a keyboard and no window manager.

The full detail is in [interface.md](../topics/interface.md). This page is
the part you need to get a usable screen today.

---

## The three ways to ask

| | What it is | When |
|---|---|---|
| [INPUT](../commands/io/INPUT.md) | a modal form with fields | several values at once |
| [CHOOSE](../commands/io/CHOOSE.md) | a pop-up list | pick one of a few |
| a screen you draw | your own table or list | anything you will use more than twice |

Start with `INPUT`. It returns 1 if accepted and 0 if cancelled, and that
return value is the only way to tell:

```ppl
EXPORT ASK()
BEGIN
  LOCAL zr, zok;
  zr := 1;
  zok := INPUT(zr, "CIRCLE", "radius:", "in cm");
  IF zok == 0 THEN RETURN -1; END;
  RETURN CIRCAREA(zr);
END;
```

What was measured about `INPUT` decides designs, and two facts hold it:

- The variables must already exist and already have the right type; a numeric
  field takes the number as typed, and a text field demands quotes. Typing
  `"0.2"` under exam pressure is a tax on every value, so prefer numeric
  fields and a drop-down over a form of blank text cells
  ([interface.input-fields](../topics/interface.md#interface.input-fields)).
- It builds its labels once, so a label that depends on another field of the
  same form cannot change while the form is open
  ([interface.input-modal](../topics/interface.md#interface.input-modal)).

## Drawing, and the trap in it

```ppl
EXPORT TDRAW()
BEGIN
  LOCAL zk;
  RECT();                                                  // clear the screen
  TEXTOUT_P("area = 12.57", 4, 40, 3, RGB(0,0,0), 312);    // x 4, y 40, font 3
  REPEAT zk := GETKEY; UNTIL zk < 0;       // then wait for a key: without it
  REPEAT zk := GETKEY; UNTIL zk >= 0;      // the drawing is gone at once
  RETURN 0;
END;
```

The screen is 320 × 240. Your area is y from 0 to 212; the rows below, 213 to
239, belong to the labels along the bottom
([interface.geometry](../topics/interface.md#interface.geometry)).

> Text that does not fit raises no error. It is painted over whatever is next
> to it, and you never learn what it said.

That is why the example passes [TEXTOUT_P](../commands/drawing/TEXTOUT_P.md)
its last argument, the maximum width in pixels: with it, a long string stays
in its column
([interface.textout-width](../topics/interface.md#interface.textout-width)).
`hpprime lint` warns when it is missing.

## Reading keys

```ppl
zk := GETKEY;      // the usual form; GETKEY() works too
```

> [GETKEY](../commands/io/GETKEY.md) returns a key's position, not a
> character. `[Enter]` is 30, not 13, and the same code means different things
> in different modes
> ([interface.getkey-position](../topics/interface.md#interface.getkey-position)).

The codes you will want first: `[Esc]` 4, `[Enter]` 30, and the arrows up 2,
down 12, left 7 and right 8. All 51 are in
[interface.key-codes](../topics/interface.md#interface.key-codes).

The six labels along the bottom are not keys. Touching one reports nothing
through `GETKEY`: a touch arrives through [MOUSE](../commands/io/MOUSE.md).
Published apps that let the keyboard drive those labels as well pick six
physical keys for them, codes 0, 5, 10, 1, 6 and 11
([interface.soft-labels-not-keys](../topics/interface.md#interface.soft-labels-not-keys)).

To wait for a key, drain the buffer first. The key that accepted your last
dialog is often still pending, and without draining, the wait returns
instantly
([interface.drain-then-wait](../topics/interface.md#interface.drain-then-wait)):

```ppl
EXPORT TPAUSE()
BEGIN
  LOCAL zk;
  REPEAT zk := GETKEY; UNTIL zk < 0;    // drain what is pending
  REPEAT zk := GETKEY; UNTIL zk >= 0;   // and only now wait
  RETURN zk;
END;
```

To find a key's code, a few lines are enough:

```ppl
EXPORT TKEY()
BEGIN
  LOCAL zk;
  RECT(); TEXTOUT_P("Press a key...", 4, 40, 3, RGB(0,0,0), 312);
  zk := TPAUSE();
  RECT(); TEXTOUT_P("code = " + STRING(zk), 4, 40, 4, RGB(0,0,0), 312);
  TPAUSE();
  RETURN zk;
END;
```

## What can be tested on the PC

You cannot test drawing on your PC. What `hpprime run` can test is any function
that decides without drawing: which row is selected, what text goes in it, what
a key means. Keeping those apart from the drawing is one way to build a screen,
and [patterns.md](../patterns.md#logic-apart-from-pixels) says what it solves
and what it costs.

The interpreter on the PC is built for it: `TEXTOUT_P`, `RECT`, `INPUT`,
`CHOOSE`, `MSGBOX`, `WAIT` and `GETKEY` are recorded instead of drawn and
return a neutral value, so a program with an interface still runs end to end
([`tools.md`](../tools.md#run)). `GETKEY`'s neutral value is "no key", so a
loop that waits for a key, like `TPAUSE`, never finishes there: `hpprime run`
stops it and says why. That part is the calculator's to test.

## Two behaviours that will confuse you

The touch that arrives twice. A dialog's OK button sits on top of the row of
labels, in the F6 position. If your finger is still there when the dialog
closes, the same touch reaches the screen underneath as though you had pressed
its F6. The fix is a debounce with memory, and
[interface.dialog-touch-twice](../topics/interface.md#interface.dialog-touch-twice)
describes it.

A program that draws and then returns leaves you looking at Home and its
return value, not at the drawing
([interface.draw-then-return](../topics/interface.md#interface.draw-then-return)).
Anything meant to be read has to wait for a key before it returns, which is
what `TDRAW`'s two loops and `TKEY`'s second `TPAUSE` do. `hpprime lint` warns
on an exported program that draws and nowhere waits.

## Before you build something big

A scrolling list, a menu with more than six actions, a text viewer: somebody
has published each of those. [libraries.md](../topics/libraries.md) says
which level a screen needs and what those libraries provide, so that you can
decide before writing rather than after.

---

Next: [4. Wrapping it as an app](04-first-app.md).

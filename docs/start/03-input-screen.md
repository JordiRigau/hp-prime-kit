# 3. Asking for data and drawing

Your program works. Now it has to talk to somebody. This is where the Prime
stops being a small computer and starts being a calculator with a screen,
six buttons and no window manager.

Full detail is in [interface.md](../reference/interface.md); this page is the
part you need to get a usable screen today.

---

## The three ways to ask

| | What it is | When |
|---|---|---|
| `INPUT` | a modal form with fields | several values at once |
| `CHOOSE` | a pop-up list | pick one of a few |
| a screen you draw | your own table or list | anything you will use more than twice |

Start with `INPUT`. It returns **1 if accepted, 0 if cancelled**, and that
return value is the only way you know:

```ppl
EXPORT ASK()
BEGIN
  LOCAL zr, zok;
  zr := 1;
  zok := INPUT(zr, "CIRCLE", "radius:", "in cm");
  IF zok == 0 THEN RETURN -1; END;
  RETURN AREA(zr);
END;
```

Three things about `INPUT` that decide designs, all measured:

- **The variables must already exist and already have the right type.**
- **It builds its labels once.** A label that depends on another field of the
  same form cannot be refreshed while the form is open.
- **A numeric field takes the number as typed. A text field demands
  quotes.** Typing `"0.2"` under exam pressure is a tax on every value, so
  prefer numeric fields plus a drop-down over a form of blank text cells.

## Drawing, and the trap in it

```ppl
RECT();                                       // clear the screen
TEXTOUT_P("area = 12.57", 4, 40, 3);          // text at x=4, y=40, font 3
```

The screen is 320 × 240. Your area is y from 0 to 212; the bottom rows
(213-239) belong to the soft-key row.

> **Text that does not fit raises no error.** It is painted over whatever is
> next to it, and you never learn what it said.

`TEXTOUT_P` takes a **seventh argument: the maximum width in pixels**. Pass
it. With it, a long string is truncated but stays in its column; without it,
it bleeds across the screen.

## Reading keys

```ppl
zk := GETKEY;      // no parentheses in PPL
```

> **`GETKEY` returns a key position, not a character.** `[Enter]` is **30**,
> not 13. And the same code means different things in different modes.

The codes you will want first: `Esc` 4, arrows ▲▼◄► 2, 12, 7, 8, soft keys
1..6 → 0, 5, 10, 1, 6, 11. The full table, with how confident each one is, is
in [interface.md](../reference/interface.md#5-the-keyboard).

To wait for a key, **drain the buffer first**. The key that accepted your
last dialog is often still pending, and without draining, your "wait" returns
instantly:

```ppl
EXPORT TPAUSE()
BEGIN
  LOCAL zk;
  REPEAT zk := GETKEY; UNTIL zk < 0;    // drain what is pending
  REPEAT zk := GETKEY; UNTIL zk >= 0;   // and only now wait
  RETURN zk;
END;
```

Do not know a key's code? Three lines tell you:

```ppl
EXPORT TKEY()
BEGIN
  LOCAL zk;
  RECT(); TEXTOUT_P("Press a key...", 4, 40, 3);
  zk := TPAUSE();
  RECT(); TEXTOUT_P("code = " + STRING(zk), 4, 40, 4);
  TPAUSE();
  RETURN zk;
END;
```

## The habit that makes this testable

You cannot test drawing on your PC. You *can* test everything that decides
**what** gets drawn and **what** each key does -- which is most of the work:

```
  pure logic          |  pixels
  --------------------|-------------------
  which row is        |  TEXTOUT_P
  selected            |  RECT
  what text goes      |  GETKEY
  in each row         |  DRAWMENU
  what a key means    |
```

Keep the right-hand column as thin as you can. Then
`hpprime run` exercises the left-hand one, and the calculator only has to
confirm the drawing.

The kit's interpreter helps here on purpose: `TEXTOUT_P`, `INPUT`, `CHOOSE`,
`MSGBOX` and `WAIT` are recorded instead of drawn, and return a neutral
value, so a program with an interface still runs end to end on your PC.

## Two things that will confuse you

**The touch that arrives twice.** A dialog's OK button sits right on top of
the soft-key row, in the F6 position. If your finger is still there when the
dialog closes, the same touch reaches the screen underneath, as though you
had pressed its F6. The fix is a debounce with memory --
[interface.md](../reference/interface.md#6-touch-and-the-touch-that-arrives-twice)
has one you can copy.

**A blank app has no view to rest in**, so `[Num]` and `[View]` will not
reach your program. Draw your own menu and read the keys yourself. That
matters in [step 4](04-first-app.md).

---

**Next:** [4. Wrapping it as an app](04-first-app.md).

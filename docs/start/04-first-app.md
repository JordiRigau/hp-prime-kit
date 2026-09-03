# 4. Wrapping it as an app

An app is your program with an icon under `[Apps]`: **two presses to open**
instead of four and some navigating. Under exam pressure that is the whole
difference, and it is almost the only reason to bother.

Which is why you do it **last**, when the program already works. The
`.hpappdir` is a container, not a rewrite.

Full detail in [apps.md](../reference/apps.md).

---

## Build it

```bash
hpprime build CIRCLEAPP CIRCLE.txt --ppl
```

That gives you a folder:

```
CIRCLEAPP.hpappdir/
   CIRCLEAPP.hpapp        settings, and the startup view
   CIRCLEAPP.hpappnote    the note
   CIRCLEAPP.hpappprgm    your program, inside
```

Drag the **folder** onto the calculator in the CK window, exactly as you
dragged the program. Then `[Apps]` → your icon.

Want an icon? `--icon icon.png`. Draw it at 73 × 74 (draw at 4× and scale
down; at that size an unsmoothed curve looks jagged). Without one the app
still works, with the generic icon.

## The three files you did not write

None of the three wrappers has the app's name inside it -- the name comes
from the folder and the file names. That is why one set works for any app,
and why the kit can ship them. They come from apps that start correctly on a
G2.

You will not touch them. But you do need to know what they do, because of the
next section.

## The failure that will happen to you

You open your app and get **the Python console**, or the wrong screen,
instead of what you built.

It is not your code. It is the last four bytes of the `.hpapp`, which say
which view the app starts in. And here is how they change behind your back:

> On the way out of an app, **the calculator rewrites the three wrappers** to
> save its state, including the view you were last in. If the Connectivity
> Kit then brings that folder back to your PC, that state lands in your
> repository, and from then on the app opens where you left it.

The structural fix is already in the tool: the wrappers are rebuilt from the
templates on **every** build. And you can check for the drift before the app
tells you:

```bash
hpprime verify CIRCLEAPP.hpappdir CIRCLE.txt
```

Exit code 1 if the folder has stopped being the one you would generate. Put
it in whatever script you use and you will never chase this bug.

Pass the source, as above, and it checks the program inside the app as well
as the wrappers. Without it, it checks the wrappers and says so.

## If your app is PPL, read this before designing the screen

An app created with base *None* -- which is what a PPL app is -- has no view
to rest in:

- if `START()` **returns**, the calculator falls back to Home, and `[Num]`
  and `[View]` no longer reach your app at all;
- if `START()` **does not return**, the `Num()` and `View()` hooks are never
  called, because your loop is holding the keyboard.

So the hooks are no use here. But the keys themselves are: while your loop
polls `GETKEY`, `[View]` arrives as **9** and `[Num]` as **11** (measured on
a G2). Draw a menu on screen, put a footer like
`key=form  View=menu  Esc=exit`, and let your program decide what each code
does.

The hooks the calculator will call for you, if you export them:

```ppl
EXPORT START()      // when the app opens
BEGIN  MAIN();  END;

EXPORT Num()        // the [Num] key: the biggest, easiest one to find
BEGIN  MAIN();  END;

EXPORT Info()       // [Shift][Apps]. Only accepts PRINT
BEGIN  PRINT("what this app does");  END;
```

## The pattern worth copying

**Let the app be only a launcher.** Keep the engine and the interface as
catalogue programs and have the app call them. Two reasons, both practical:

1. **What an app's program exports is tied to that app.** If your engine has
   to be reusable from elsewhere, it has to live in a catalogue program.
2. **Global names collide**, so the app and the interface need different
   names anyway.

The cost is installing three things instead of one. The gain is that the part
that never changes -- your data -- is not touched when you fix the interface.

## Honest status

Both kinds have now been opened on a G2. A **Python** app starts in its own
screen, and a **PPL** app built end to end by this tool appears under
`[Apps]`, runs `START()`, computes correctly and keeps its accented text.

What is still worth reporting, if you try it: whether the same holds on a
**G1**, and what the six on-screen soft-key positions return as key codes --
[one of those numbers is still ambiguous](../reference/interface.md#5-the-keyboard).
[examples/apptest/](../../examples/apptest/) prints whatever you press.

---

**Next:** [5. Moving to Python](05-python.md), when PPL starts to fight you.

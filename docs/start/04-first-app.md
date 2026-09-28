# 4. Wrapping it as an app

An app is your program with an icon under `[Apps]`: two presses to open it
instead of four and some navigating. Under exam pressure that is the whole
difference, and it is close to the only reason to bother.

That is also why you do it last, once the program works. The `.hpappdir` is a
container, not a rewrite.

The full detail is in [apps.md](../topics/apps.md).

---

## Build it

```bash
hpprime build CIRCLEAPP programs/CIRCLE/CIRCLE.txt --ppl -o programs/CIRCLE
```

That gives you a folder, beside the program in `programs/CIRCLE/`
([apps.hpappdir-contents](../topics/apps.md#apps.hpappdir-contents)):

```
CIRCLEAPP.hpappdir/
   CIRCLEAPP.hpapp        settings, and the startup view
   CIRCLEAPP.hpappnote    the note
   CIRCLEAPP.hpappprgm    your program, inside
```

Drag the folder onto the calculator in the CK window, exactly as you dragged
the program, and not into the mirror. Then `[Apps]` and your icon
([apps.install](../topics/apps.md#apps.install)).

For an icon, pass `--icon icon.png`, drawn at 73 × 74. Without one the app
still works and gets the generic icon
([apps.icon](../topics/apps.md#apps.icon)).

## The three files you did not write

None of the three wrappers has the app's name inside it. The name comes from
the folder and the file names, which is why one set works for any app and why
the tools can ship them. They come from apps that run on a G2
([apps.wrappers-are-portable](../topics/apps.md#apps.wrappers-are-portable)).

You will not touch them, but you need to know what they do, because of the next
section.

## The startup view, and how it changes behind your back

The symptom, in a Python app, is that you open it and get the Python console
instead of what you built.

The cause is not your code. It is the last four bytes of the `.hpapp`, which
say which view the app starts in
([apps.startup-view-byte](../topics/apps.md#apps.startup-view-byte)):

> On the way out of an app, the calculator rewrites the three wrappers to save
> its state, including the view you were last in. If the Connectivity Kit then
> brings that folder back to your PC, that state lands in your repository, and
> from then on the app opens where you left it.

`hpprime build` rebuilds the wrappers from the templates every time, and you
can check for the drift before the app shows it to you:

```bash
hpprime verify programs/CIRCLE/CIRCLEAPP.hpappdir programs/CIRCLE/CIRCLE.txt
```

It exits 1 if the folder has stopped being the one you would generate
([`tools.md`](../tools.md#write--read--verify)). Passing the source, as above,
checks the program inside the app as well as the wrappers. Without it, it
checks the wrappers and says so.

## If your app is PPL, read this before designing the screen

An app created with base *None*, which is what a PPL app is, has no view to
rest in:

- if `START()` returns, the calculator falls back to Home, and `[Num]` and
  `[View]` no longer reach your app at all;
- if `START()` does not return, the `Num()` and `View()` hooks are never
  called, because your loop is holding the keyboard
  ([apps.blank-app-hooks](../topics/apps.md#apps.blank-app-hooks)).

So the hooks are no use here, but the keys are. While your loop polls
`GETKEY`, `[View]` arrives as 9 and `[Num]` as 11
([apps.blank-app-keys](../topics/apps.md#apps.blank-app-keys)). Draw a menu
on screen, add a footer such as `key=form  View=menu  Esc=exit`, and let your
program decide what each code does.

The hooks the calculator will call, if you export them
([apps.hooks](../topics/apps.md#apps.hooks)):

```ppl
EXPORT START()      // when the app opens
BEGIN  MAIN();  END;

EXPORT Num()        // the [Num] key
BEGIN  MAIN();  END;

EXPORT Info()       // [Shift][Apps]
BEGIN  PRINT("what this app does");  END;
```

`Info()` has been seen to accept `PRINT`; what else it accepts has not been
tried.

## Keep the app a launcher

Keep the engine and the interface as catalogue programs and have the app call
them. Two reasons:

1. What an app's program exports is tied to that app, so an engine that has
   to be reusable from elsewhere has to live in a catalogue program
   ([apps.exports-tied](../topics/apps.md#apps.exports-tied)).
2. Exported names are global and collide, so the app and the interface need
   different names anyway
   ([ppl.global-namespace](../topics/ppl.md#ppl.global-namespace)).

The cost is installing three things instead of one, in dependency order
([ppl.compilation-order](../topics/ppl.md#ppl.compilation-order)). The gain is
that the part which never changes, your data, is not touched when you fix the
interface.

## What has been checked

A PPL app built end to end by `hpprime build --ppl` appears under `[Apps]` on
a G2, runs `START()`, computes correctly and keeps its accented text, and the
Python app wrappers start a Python app in its own screen
([apps.generated-and-verified](../topics/apps.md#apps.generated-and-verified)).
Neither has been tried on a G1. The app that was run is `examples/apptest/`
in the repository, if you want to repeat it on yours.

---

Next: [5. Moving to Python](05-python.md), for when PPL starts to fight you.

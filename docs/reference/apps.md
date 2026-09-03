# Apps

A loose program lives in the catalogue and opens with `[Shift][Program]` +
navigate + `[Enter]`. An **app** has an icon under `[Apps]`, so opening it is
**two presses**. Under exam pressure that is the whole difference, and it is
almost the only reason to wrap something as an app.

> **The rule that pays for itself**: develop as a **program** and wrap it as
> an app at the end. The engine and the interface are identical either way,
> the `.hpappdir` is only a container, and iterating on a program is much
> faster.

---

## 1. What is inside a `.hpappdir`

An app is a **folder** whose name ends in `.hpappdir`. The app's name comes
from the folder name and the file names: **none of the three wrappers has the
name written inside it**. That is why the same three, byte for byte, work for
any app: they are copied and renamed.

```
MYAPP.hpappdir/
   MYAPP.hpapp        app settings, and the STARTUP VIEW
   MYAPP.hpappnote    the note  (2 bytes when empty: 00 00)
   MYAPP.hpappprgm    the app's PPL program -- same format as .hpprgm
   icon.png           the icon (optional)
   *.py               the modules, if it is a Python app
   *.png              any other file the app wants to carry
```

Measured on the apps installed on a real G2:

| App | `.hpapp` | `.hpappprgm` | What it is |
|---|---|---|---|
| `&Python` (factory) | 180 B | 1152 B | Python app, empty program |
| `&Function` (factory) | 1699 B | 1152 B | factory app with its own base |
| a user copy of a factory app | 1344 B | 1152 B | inherits that app's settings |
| a user blank app with PPL | **124 B** | 27322 B | **blank** app, code in the program |
| `MarkdownViewer` | 188 B | 1152 B | Python app |

Two things to read out of that table:

- **An `.hpappprgm` of 1152 bytes** is the signature of *"empty program"*:
  just the symbol table with a `Main` and no source. Every Python app has it,
  because its code is in the `.py` files.
- **The small `.hpapp` (124 B) is the one from an app with base *None*.**
  Apps that inherit from a factory app drag that app's settings along and
  weigh ten times as much.

HP's `Gallery` also carries three loose PNGs of up to 300 KB, so **the folder
accepts arbitrary files**: that is the mechanism a Python app uses to carry
its modules.

## 2. The startup-view byte

The most baffling failure a Python app has: you open it and get **the Python
console** -- a list of `>import …` from previous runs -- instead of your
screen.

It is not the code. It is the `.hpapp`, in its **last four bytes**:

```
a skeleton that works  ...  08 00 00 00   85 06 C9 00   01 00 00 00
factory &Python        ...  08 00 00 00   85 06 C9 00   03 00 00 00
                               length        tag           view
```

`01` is the app's own view; `03` is the Numeric view, which in a Python app
**is the console**. The factory `&Python` app carries `03` because its screen
*is* the terminal -- so the value is not wrong, it is copied from the wrong
place.

**How it gets there by itself**: on the way out of an app, the calculator
**rewrites the three wrappers** to save state, including the view you were
in. If the Connectivity Kit then brings that folder back to the PC, that
state enters your repository, and from then on the app opens where you left
it.

**The structural fix, not the patch**: keep the good wrappers separately and
**rebuild them on every build**. That is what `hpprime build` does, and
`hpprime verify` warns that the folder has stopped matching the templates --
that is, that the calculator has rewritten them -- before the app tells you.

## 3. The icon

`icon.png`, inside the folder. Measured:

| File | Size |
|---|---|
| `Gallery.hpappdir/icon.png` (HP's) | **73 × 74**, RGBA |
| a user icon, after a round trip through the calculator | **37 × 38**, RGBA |

So: ship it at 73 × 74 and the calculator keeps a half-size copy. Both
measurements are from real files, not from documentation, which does not say.
Draw at 4× and scale down: at 73 px, a curve without supersampling comes out
jagged.

Without `icon.png` the app still appears, with the generic icon.

## 4. The two kinds of app

| | **PPL** app | **Python** app |
|---|---|---|
| Where the code lives | inside the `.hpappprgm` | in the folder's `.py` files |
| `.hpappprgm` | the program, with its source | empty (1152 B), with a `Main` |
| Generated from the PC | `hpprime build --ppl` | copy the `.py` files, done |
| Edited on the calculator | yes, with its editor | yes, with the Python editor |
| Calls the other side | `PYTHON("script")` | `hpprime.eval("…")` |

The Python one is **far easier to generate**: the modules are text files
copied as they are, with no binary format in the way.

For the bridge between the two sides, see [micropython.md](micropython.md).

## 5. PPL apps: the hooks, and the blank-app trap

An app's program can export functions with reserved names that the calculator
calls on its own:

```ppl
EXPORT START()      // when the app opens
BEGIN  MYPROGRAM();  END;

EXPORT Num()        // the [Num] key: the biggest, easiest one to find
BEGIN  MYPROGRAM();  END;

EXPORT Info()       // [Shift][Apps]. Only accepts PRINT
BEGIN  PRINT("what this app does");  END;

EXPORT RESET()      // put the globals back as they started
BEGIN  MYVAR := 1;  END;
```

And here is the trap:

> An app created with **Base App: None** has no view to rest in.
>
> - If `START()` **returns**, the calculator falls back to Home, and then
>   `[Num]` and `[View]` no longer reach the app at all.
> - If `START()` **does not return** (it sits in a loop), the `Num()` and
>   `View()` hooks are never called: the loop is holding the keyboard.
>
> Either way, **the hooks are no use to a blank app**.

What does work, and it is what makes the whole thing tractable: while
`START()` is polling `GETKEY`, **both keys arrive as ordinary key codes**.
Measured on a G2, in an app built end to end by this kit: `[View]` is **9**
and `[Num]` is **11**.

So do not treat the view keys as hooks -- treat them as keys. Draw the menu
on screen, put a footer like `key=form  View=menu  Help=help  Esc=exit`, and
let the program decide what each code does. See
[interface.md](interface.md#5-the-keyboard).

### The launcher pattern

Worth copying: **the app is only a launcher**. The engine and the interface
stay as catalogue programs, and the app just calls them.

Two reasons, both practical:

1. **What an app's program exports is tied to that app.** If the engine has
   to be reusable from another app or from Home, it has to live in a
   catalogue program.
2. **Global names collide.** The app and the interface program need different
   names: two global symbols with the same name cannot coexist.

The cost of splitting it in three is that you install three things. The
benefit is that the block that never changes -- the data, which can be
hundreds of kilobytes -- is not touched when you fix the interface.

## 6. Python apps: how one is put together

### Creating the first one

On the calculator: `[Apps]` → **Python** → **(Save)** key → a new name. That
gives you a Python app under your name, and the Connectivity Kit then has the
folder and the three good wrappers.

For a blank PPL app: `[Apps]` → **(Save)** → *Base App*: **None** → name.

The kit ships the wrappers in [templates/app/](../../templates/app/), so you
do not need to do even that to start. They are **two different descriptors**,
because they are not interchangeable:

| File | | Where it comes from |
|---|---|---|
| `python.hpapp` | 188 B | an app **based on the Python app** |
| `blank.hpapp` | 124 B | an app created with **Base App: None**, which is the shape a PPL app has |
| `note.hpappnote` | 2 B | the empty note |
| `program.hpappprgm` | 1152 B | the empty program, with its `Main` |

`hpprime build` picks the right one: Python by default, blank with `--ppl`.
`--base` passes another, including a `.hpapp` of your own.

Neither carries text inside -- that has been checked -- so they bring nothing
from the app they came from beyond its settings.

### The entry point is `main.py`

In every Python app examined, the file is called `main.py` and **its code is
at module level**, not inside an `if __name__`: it runs on import. The
Markdown Viewer ends literally like this:

```python
try:
    main()
except KeyboardInterrupt:
    clear_screen()
```

`KeyboardInterrupt` is the `[ON]` key, which is how you break out of a loop.

### The structure that works

The rule that orders it is **separate what can be tested on the PC from what
cannot**:

| File | What it is | Tested on the PC? |
|---|---|---|
| `engine.py` | the calculation | **yes** -- it is the *same file* as on the PC |
| `project.py` | the state while it is being assembled | yes |
| `list.py` | selection, window, keys: pure logic | yes |
| `views.py` | what text goes in each row | yes |
| `geometry.py` | numbers only: where each column goes | yes, and a test uses it |
| `data.py` | the layer that crosses the bridge | **no** |
| `screen.py` | pixels and keys | **no** -- which is why it is as thin as possible |
| `main.py` | wiring it together | no |

The trick that makes this work: `data.py` has **two versions with the same
face**, one over a PC engine and one over the PPL bridge. Because of that,
`engine.py` is literally the same file in both places, and the checks it
passes on the PC say something about what runs on the calculator.

### Assembling it

Copying by hand guarantees that sooner or later the two files stop being the
same. So copy them with a command, and **have a check that they have not
drifted apart**: `hpprime verify`.

Three details that tool handles and that are otherwise forgotten:

- **rebuild the three wrappers** from the templates (§2);
- **delete `__pycache__`**: those are CPython `.pyc` files, which MicroPython
  would not read, and they only add bulk;
- **check the imports**: a shared module cannot import anything MicroPython
  does not have. `__future__` does not exist, nor `os` or `sys` in the same
  way. It is a failure you do not see until the app starts -- and then it
  closes without a word.

## 7. Installing

Same as a program, with the same two traps:

1. Open the **Connectivity Kit** with the calculator connected (or the
   Virtual Calculator).
2. **Drag the `.hpappdir` folder** from the file manager **onto the
   calculator** in the CK window.
3. On the calculator: `[Apps]` → your app.

> **Do not copy it into
> `Documents\HP Connectivity Kit\Calculators\<calculator>\`.** That folder is
> a **mirror** the CK writes *from* the calculator: on connecting it
> overwrites it and your copy disappears. And if the drag shows the **no-entry
> cursor**, check whether the CK is set to run **as administrator**. Both
> cases, with the evidence, in [deploy.md](deploy.md).

Once installed, moving it to another calculator is a drag **inside** the CK,
from one to the other. The Prime also supports direct calculator-to-calculator
transfer over USB OTG.

## 8. Generating and checking it from the PC

```bash
# a whole Python app: wrappers + modules + icon
hpprime build MYAPP src/*.py --icon icon.png

# rebuild it, and warn if the calculator has rewritten the wrappers
hpprime verify MYAPP.hpappdir src/*.py

# a PPL app: the source goes into the .hpappprgm, descriptor is the blank one
hpprime build MYAPP app.txt --ppl
```

### What is verified and what is not

| | |
|---|---|
| The generated `.hpappprgm` reads back as the same source | **yes**, and the tool checks it before writing |
| A program generated from Python **runs on an HP Prime** | **yes** -- see [deploy.md](deploy.md) |
| The Python app wrappers start it in its own screen | **yes**: they come from an app that runs on this calculator |
| A **PPL** app assembled end to end by the builder | **yes**, on a G2: it appears under `[Apps]`, `START()` runs, the program inside computes correctly and its accented text is intact. The app that was used is [examples/apptest/](../../examples/apptest/) |

And the thing worth doing before trusting any result obtained on the
calculator: **pull the source back out and compare it with the repository**.

```bash
hpprime read ".../Calculators/HP Prime/MYAPP.hpappdir/MYAPP.hpappprgm" -o installed.txt
diff installed.txt ppl/MYAPP.txt
```

That is how you find out the installed app has been two commits behind the
code you were trusting.

## 9. What is not solved

- **Generating a `.hpapp` from scratch.** You copy one from an app that
  works. Its internal grammar is not decoded beyond the view byte, and it
  does not need to be: it carries no name inside, so one works for all.
- **The empty `.hpappprgm` is not a template for `write`.** It has no source
  block to replace, and the tool says so: *"no source block found (empty
  program?)"*. Use `templates/code.hpprgm`, which the kit ships.
- **The compiled block.** An app coming back from the calculator can carry
  a couple of kilobytes of compiled block before its source; it reads fine,
  but it is no use as a template. Detail in [formats.md](formats.md).

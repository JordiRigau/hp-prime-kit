# 2. Your first program

From an empty folder to a function running on the calculator. Seven steps, five
of them on your PC.

---

## Step 1 — write it

You do not need an editor on the calculator. A PPL program is text.

```bash
hpprime new CIRCLE
```

That writes `programs/CIRCLE/CIRCLE.txt`. What you make goes in `programs/`,
one folder each, and the commands below give its path from the repository's
folder. Open it: it is a working program, not a stub. Its comments aside, it is
this:

```ppl
EXPORT CIRCAREA(zr)
BEGIN
  RETURN 3.14159265359 * zr * zr;
END;

EXPORT MAIN()
BEGIN
  LOCAL zr;
  zr := 1;
  INPUT(zr, "CIRCLE", "radius:");
  MSGBOX("area = " + STRING(CIRCAREA(zr)));
  RETURN CIRCAREA(zr);
END;
```

Five rules of the language are already in those lines, each a fact with its
evidence:

| In the program | The rule |
|---|---|
| `EXPORT` | makes a function visible from Home and from every other program, in one shared namespace, which is why the name has a prefix: `AREA` is already the Function app's [AREA](../commands/function/AREA.md) ([ppl.global-namespace](../topics/ppl.md#ppl.global-namespace)) |
| `LOCAL zr;` first | every local is declared at the top of the `BEGIN` ([ppl.locals-at-top](../topics/ppl.md#ppl.locals-at-top)) |
| `zr := 1;` | `:=` assigns and `==` compares ([ppl.equality-operators](../topics/ppl.md#ppl.equality-operators)) |
| `END;` | `END` closes every block: there is no `ENDIF` ([ppl.no-end-keywords](../topics/ppl.md#ppl.no-end-keywords)) |
| the `;` after `END` | it is required, and a missing one is reported on the next line ([ppl.end-semicolon](../topics/ppl.md#ppl.end-semicolon)) |

The split between the two functions is the point of the file. `CIRCAREA` is
pure arithmetic and `MAIN` talks to the screen, so everything on the
`CIRCAREA` side can be tested on your PC. Keeping that line as the program
grows is what makes this platform workable.

## Step 2 — lint it, before compiling anything

```bash
hpprime lint programs/CIRCLE/CIRCLE.txt
```

It should say `0 error(s), 0 warning(s)`. The linter catches, before the
calculator does, what its compiler will not explain. Every finding names the
fact it comes from and how that fact is known. It is an error only as far as
the measurement behind it reaches, and a warning where the rule goes further
than anybody has measured; a name that is not on HP's list of names is a
warning too, because that is how an invented command shows up. What each rule
catches is in [`tools.md`](../tools.md#lint). Fix what it reports now: on the
calculator the same mistake costs a round trip.

## Step 3 — run it, on your PC

```bash
hpprime run programs/CIRCLE/CIRCLE.txt --call "CIRCAREA(2)"
```

You should get `12.5663706144`. This runs the file you are going to install,
not a copy of it rewritten for the PC, through an interpreter that covers a
subset of PPL and raises on anything outside it rather than inventing a result
([`tools.md`](../tools.md#run)). It is not the calculator. The one way to know
that the two agree on a call is to run it on both, which is what
[`hpprime compare`](../tools.md#compare) does.

Try the interface half too:

```bash
hpprime run programs/CIRCLE/CIRCLE.txt --call "MAIN()"
```

It answers `3.1415926536`, the area for the radius `MAIN` starts with.
[INPUT](../commands/io/INPUT.md) and [MSGBOX](../commands/io/MSGBOX.md) are
not drawn, because there is no screen here: they are recorded and return a
neutral value, so the calculation runs without an interface. See
[what can and cannot be tested](../topics/interface.md#what-the-design-of-a-screen-comes-down-to).

## Step 4 — turn it into a `.hpprgm`

```bash
hpprime write programs/CIRCLE/CIRCLE.txt -o programs/CIRCLE/CIRCLE.hpprgm
```

`.hpprgm` is a binary container with the source inside it verbatim
([formats.container](../topics/formats.md#formats.container)). `write` builds
one from the template that ships with the tools, and reads it back before
reporting success. A program made this way, never touched by the Connectivity
Kit, has been loaded and run on a G2
([deploy.writer-on-hardware](../topics/deploy.md#deploy.writer-on-hardware)).

## Step 5 — put it on the calculator

1. Connect the calculator, or open the Virtual Calculator, and open the
   Connectivity Kit.
2. Drag `CIRCLE.hpprgm`, in `programs/CIRCLE/`, from your file manager onto
   the calculator in the CK window.

> Do not copy it into the mirror folder. It looks like a mailbox and it is not:
> on connecting, the CK overwrites it with whatever is on the calculator, and
> your file disappears
> ([deploy.ck-mirror](../topics/deploy.md#deploy.ck-mirror)).

If the drag shows the no-entry cursor and nothing happens, the file is not the
problem: check whether the CK is set to run as administrator
([deploy.drag-refused-when-elevated](../topics/deploy.md#deploy.drag-refused-when-elevated)).

On the Virtual Calculator there is a second way, with no drag:
[`hpprime install programs/CIRCLE/CIRCLE.hpprgm --restart`](../tools.md#install--pull) copies
it into the emulator's own folder, which, unlike the mirror, is read when the
emulator starts
([deploy.emulator-folder](../topics/deploy.md#deploy.emulator-folder)). A
program that arrives that way has to be compiled once before its name works
on Home: `[Shift][Program]`, pick it, *Edit*, *Check*, `[Esc]`
([deploy.compile-once-after-a-file-copy](../topics/deploy.md#deploy.compile-once-after-a-file-copy)).

## Step 6 — run it there

A program dragged over in the CK runs as it is, with nothing to compile
([deploy.no-manual-compile](../topics/deploy.md#deploy.no-manual-compile)).

On the Home screen, type the function name and its arguments:

```
CIRCAREA(2)
```

and press `[Enter]`. You should get 12.566…

Then run the interface half, and note the missing parentheses:

```
MAIN
```

> On Home, a function with no arguments is called without parentheses:
> `MAIN()` answers *syntax error* and `MAIN` runs it. Inside your source the
> parentheses are right, and `CIRCAREA(zr)` is called normally from `MAIN`, so
> this is a rule of Home rather than of PPL
> ([ppl.home-no-parentheses](../topics/ppl.md#ppl.home-no-parentheses)).

It is the first failure most people meet, and it is not in your program.

## Step 7 — check that you installed what you think you did

The source can be read back out of what is installed and compared with yours
([deploy.read-it-back](../topics/deploy.md#deploy.read-it-back)). From a
physical calculator, through the mirror, which is fine to read:

```bash
hpprime read ".../Calculators/HP Prime/CIRCLE.hpprgm" -o programs/CIRCLE/installed.txt
diff programs/CIRCLE/installed.txt programs/CIRCLE/CIRCLE.txt
```

The only difference should be the trailing newline: the calculator stores the
editor's buffer, which has none
([formats.line-endings](../topics/formats.md#formats.line-endings)).

From the Virtual Calculator it is one command, which exits 1 when what is
installed is not your file:

```bash
hpprime pull CIRCLE --diff programs/CIRCLE/CIRCLE.txt
```

This is the check that catches a calculator still running an old version.

---

## What will break on your first day

Each row links to the fact that says how it is known. The last column is what
[`hpprime lint`](../tools.md#lint) does about it before you open the CK.

| What you do | What happens | Instead | Known from | `hpprime lint` |
|---|---|---|---|---|
| `LOCAL` with 9 names | *syntax error* on that line | at most 8 per `LOCAL`; use groups of 6 | [ppl.local-limit](../topics/ppl.md#ppl.local-limit) | error from 9, warning at 7 and 8 |
| `ENDIF`, `ENDFOR`, `ENDWHILE` | *syntax error* | `END` for everything | [ppl.no-end-keywords](../topics/ppl.md#ppl.no-end-keywords) | error |
| `END` without its `;` | *syntax error*, on a block's reported on the next line | `END;` | [ppl.end-semicolon](../topics/ppl.md#ppl.end-semicolon) | error |
| `za = 2;` meaning to assign | nothing is assigned, and no error | `za := 2;` | [ppl.equality-operators](../topics/ppl.md#ppl.equality-operators) | a warning |
| `n := SIZE(M)(1);` | *syntax error* | `zd := DIM(M);` then `zd(1)` | [ppl.index-call](../topics/ppl.md#ppl.index-call) | error |
| a `LOCAL` half way down a function | *syntax error* | all of them at the top of the `BEGIN` | [ppl.locals-at-top](../topics/ppl.md#ppl.locals-at-top) | error |
| `L(0)` on a list | its **last** element, with no error | positions count from 1 | [ppl.one-based](../topics/ppl.md#ppl.one-based) | a warning |
| `MAIN()` on Home | *syntax error* | `MAIN`, with no parentheses | [ppl.home-no-parentheses](../topics/ppl.md#ppl.home-no-parentheses) | cannot see Home |
| a program that draws, then returns | you see Home and the returned value, not the drawing | wait for a key before returning | [interface.draw-then-return](../topics/interface.md#interface.draw-then-return) | a warning |
| copying the file into the mirror | nothing is installed | drag it in the CK window | [deploy.ck-mirror](../topics/deploy.md#deploy.ck-mirror) | cannot see it |
| a program installed before the one whose functions it calls | it does not see them | install in dependency order, or recompile it | [ppl.compilation-order](../topics/ppl.md#ppl.compilation-order) | cannot see it |
| passing a big matrix to a function | it is copied | keep large data in a global | [ppl.matrices-by-value](../topics/ppl.md#ppl.matrices-by-value) | cannot see it |

A single `=` in a condition is not on the list. `IF a = 1 THEN` compiles and
compares, exactly as `==` does
([ppl.equality-operators](../topics/ppl.md#ppl.equality-operators)). It is
only as a statement that it silently does nothing.

## When something does not add up

The method matters more than the tools:

> Do not reason about the syntax. Measure programs that already work on that
> same calculator, and compare.

Two consequences:

- An error that does not move after a fix means your hypothesis is false, not
  that the fix was too small. When the editor's *Check* names a line, it is
  one of the bad lines, not necessarily the only one, and whether it is the
  first or the last depends on the error
  ([ppl.check-last-error](../topics/ppl.md#ppl.check-last-error)).
- Download somebody else's program and read it.
  [hpcalc.org](https://www.hpcalc.org/prime/) is full of code that runs on real
  calculators, and much of what the
  [interface page](../topics/interface.md#where-this-comes-from) knows was read
  there.

---

Next: [3. Asking for data and drawing](03-input-screen.md).

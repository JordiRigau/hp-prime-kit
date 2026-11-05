# Apps

Facts about the `.hpappdir`, its wrappers and its hooks, rather than about one
command. Each has an identifier, says how it is known, and is stated here
once.

A loose program lives in the catalogue and opens with `[Shift][Program]`,
navigate, `[Enter]`. An app has an icon under `[Apps]`, so opening it is two
presses, and it can have views and hooks of its own
([apps.hooks](#apps.hooks)).

How an app can be laid out -- everything in its own program, or a launcher
for programs installed beside it -- and what each way costs, is in
[patterns.md](../patterns.md). None of it is required.

For the bridge between PPL and Python, see
[micropython.md](micropython.md). Building and checking one from the PC:

```bash
hpprime build MYAPP src/*.py --icon icon.png    # a whole Python app
hpprime verify MYAPP.hpappdir src/*.py          # rebuild, and warn on drift
hpprime build MYAPP app.txt --ppl               # a PPL app
```

---

<a name="apps.hpappdir-contents"></a>
## What is inside a .hpappdir, and what the sizes say

| | |
|---|---|
| Identifier | `apps.hpappdir-contents` |
| Kind | rule |
| Known from | G2 |

An app is a folder whose name ends in `.hpappdir`. The app's name comes from
the folder name and the file names: none of the three wrappers has the name
written inside it, which is why the same three, byte for byte, work for any
app. They are copied and renamed.

```
MYAPP.hpappdir/
   MYAPP.hpapp        app settings, and the STARTUP VIEW
   MYAPP.hpappnote    the note  (2 bytes when empty: 00 00)
   MYAPP.hpappprgm    the app's PPL program -- same format as .hpprgm
   icon.png           the icon (optional)
   *.py               the modules, if it is a Python app
   *.png              any other file the app wants to carry
```

| App | `.hpapp` | `.hpappprgm` | What it is |
|---|---|---|---|
| `&Python` (factory) | 180 B | 1152 B | Python app, empty program |
| `&Function` (factory) | 1699 B | 1152 B | factory app with its own base |
| a user copy of a factory app | 1344 B | 1152 B | inherits that app's settings |
| a user blank app with PPL | 124 B | 27322 B | blank app, code in the program |
| `MarkdownViewer` | 188 B | 1152 B | Python app |

An `.hpappprgm` of 1152 bytes is the signature of an empty program: the symbol
table with a `Main` and no source, which every Python app has because its code
is in the `.py` files. The small `.hpapp`, 124 B, is the one from an app with
base *None*; apps that inherit from a factory app drag that app's settings
along and weigh ten times as much.

**Evidence.** Measured on the apps installed on a real G2 with firmware
2.4.15515. HP's `Gallery` also carries three loose PNGs of up to 300 KB, so
the folder accepts arbitrary files, which is the mechanism a Python app uses
to carry its modules.

<a name="apps.startup-view-byte"></a>
## One byte decides whether a Python app opens in your screen or the console

| | |
|---|---|
| Identifier | `apps.startup-view-byte` |
| Kind | rule |
| Known from | G2 |

The most baffling failure a Python app has -- you open it and get the Python
console, with a list of `>import …` from previous runs, instead of your screen
-- is not the code. It is the `.hpapp`, in its last four bytes:

```
a skeleton that works  ...  08 00 00 00   85 06 C9 00   01 00 00 00
factory &Python        ...  08 00 00 00   85 06 C9 00   03 00 00 00
                               length        tag           view
```

`01` is the app's own view; `03` is the Numeric view, which in a Python app is
the console. The factory `&Python` app carries `03` because its screen is the
terminal, so the value is not wrong in itself: it has been copied from the
wrong place.

It also gets there on its own. On the way out of an app the calculator
rewrites the three wrappers to save state, including the view you were in, and
if the Connectivity Kit then brings that folder back to the PC, that state
enters your repository and the app opens where you left it from then on. The
structural fix is to keep the good wrappers separately and rebuild them on
every build, which is what `hpprime build` does; `hpprime verify` warns that
the folder has stopped matching the templates before the app tells you.

**Evidence.** Measured by comparing the `.hpapp` of a skeleton that works with
the factory `&Python` one, on a G2 with firmware 2.4.15515.

<a name="apps.icon"></a>
## The icon is 73x74, and the calculator keeps a half-size copy

| | |
|---|---|
| Identifier | `apps.icon` |
| Kind | rule |
| Known from | G2 |

| File | Size |
|---|---|
| `Gallery.hpappdir/icon.png` (HP's) | 73 × 74, RGBA |
| a user icon, after a round trip through the calculator | 37 × 38, RGBA |

Ship it at 73 × 74. Draw at 4× and scale down: at 73 px, a curve without
supersampling comes out jagged. Without `icon.png` the app still appears, with
the generic icon.

**Evidence.** Measured on real files from a G2 with firmware 2.4.15515, not
from documentation, which does not say.

<a name="apps.two-kinds"></a>
## A PPL app and a Python app differ in where the code lives

| | |
|---|---|
| Identifier | `apps.two-kinds` |
| Kind | rule |
| Known from | G2 |

| | PPL app | Python app |
|---|---|---|
| Where the code lives | inside the `.hpappprgm` | in the folder's `.py` files |
| `.hpappprgm` | the program, with its source | empty (1152 B), with a `Main` |
| Generated from the PC | `hpprime build --ppl` | copy the `.py` files, done |
| Edited on the calculator | yes, with its editor | yes, with the Python editor |
| Calls the other side | `PYTHON("script")` | `hpprime.eval("…")` |

The Python one is much easier to generate: the modules are text files copied
as they are, with no binary format in the way.

**Evidence.** Measured on apps of both kinds built by `hpprime build` and installed
on a G2 with firmware 2.4.15515.

<a name="apps.hooks"></a>
## The hooks an app's program can export

| | |
|---|---|
| Identifier | `apps.hooks` |
| Kind | rule |
| Known from | G2 |

```ppl
EXPORT START()      // when the app opens
EXPORT Num()        // the [Num] key: the biggest, easiest one to find
EXPORT Info()       // [Shift][Apps]. Only accepts PRINT
EXPORT RESET()      // put the globals back as they started
```

**Evidence.** Measured on a G2 with firmware 2.4.15515, in apps built by
`hpprime build`. `Info()` accepting only `PRINT` is what that app showed; what else it
would accept was not tried.

<a name="apps.blank-app-hooks"></a>
## In a blank app the hooks are no use

| | |
|---|---|
| Identifier | `apps.blank-app-hooks` |
| Kind | rule |
| Known from | G2 |

An app created with **Base App: None** has no view to rest in. If `START()`
returns, the calculator falls back to Home, and then `[Num]` and `[View]` no
longer reach the app at all. If `START()` does not return, because it sits in
a loop, the `Num()` and `View()` hooks are never called: the loop is holding
the keyboard. Either way the hooks do not fire, and the way to build such an
app is [apps.blank-app-keys](#apps.blank-app-keys).

**Evidence.** Measured on a G2 with firmware 2.4.15515, in an app built end to
end by `hpprime build`.

<a name="apps.blank-app-keys"></a>
## The view keys still arrive as keys

| | |
|---|---|
| Identifier | `apps.blank-app-keys` |
| Kind | rule |
| Known from | G2 |

While `START()` is polling `GETKEY`, `[View]` arrives as 9 and `[Num]` as 11,
like any other key
([interface.key-codes](interface.md#interface.key-codes)). So treat the view
keys as keys rather than as hooks: draw the menu on screen, add a footer such
as `key=form  View=menu  Help=help  Esc=exit`, and let the program decide what
each code does.

**Evidence.** Measured on a G2 with firmware 2.4.15515, in an app built end to
end by `hpprime build`.

<a name="apps.exports-tied"></a>
## What an app's program exports is tied to that app

| | |
|---|---|
| Identifier | `apps.exports-tied` |
| Kind | rule |
| Known from | unverified |

An engine that has to be reusable from another app, or from Home, has to live
in a catalogue program rather than inside the app.

**Evidence.** Seen on a G2 with firmware 2.4.15515 while building an app, with
no program kept, so what exactly was tried is not known. One app and one program
calling what it exports would settle it. Together with
[ppl.global-namespace](ppl.md#ppl.global-namespace), it is why the app, the
interface and the engine are separate installs in the launcher pattern of
[patterns.md](../patterns.md#the-app-as-a-launcher).

<a name="apps.wrappers-are-portable"></a>
## The wrappers carry no name, so four templates cover every app

| | |
|---|---|
| Identifier | `apps.wrappers-are-portable` |
| Kind | rule |
| Known from | G2 |

| File | | Where it comes from |
|---|---|---|
| `python.hpapp` | 188 B | an app based on the Python app |
| `blank.hpapp` | 124 B | an app created with Base App: None, the shape a PPL app has |
| `note.hpappnote` | 2 B | the empty note |
| `program.hpappprgm` | 1152 B | the empty program, with its `Main` |

The two descriptors are not interchangeable: `hpprime build` picks Python by
default and blank with `--ppl`, and `--base` passes another, including one of
your own. To make the first of each on the calculator: `[Apps]` → **Python** →
**(Save)** → a name, or `[Apps]` → **(Save)** → *Base App*: **None** → a name.

**Evidence.** The four are in `templates/app/`, taken
from apps that run on a G2 with firmware 2.4.15515, and checked to carry no
text inside, so they bring nothing from the app they came from beyond its
settings.

<a name="apps.main-py"></a>
## A Python app runs its file by importing it, and a lone file need not be main.py

| | |
|---|---|
| Identifier | `apps.main-py` |
| Kind | rule |
| Known from | emulator |

In every Python app examined the file is called `main.py` and its code is at
module level rather than inside an `if __name__` block. That is how it runs:
the calculator imports the file, and what is at module level runs on import.
An app whose only Python file was `start.py` ran it, and its Numeric view
showed the console line `>import start`, so the name `main.py` is not what
the calculator looks for when there is one file. With several, which one it
imports was not tried, and `main.py`, the name every published app uses, is
the one to keep.

The Markdown Viewer ends with:

```python
try:
    main()
except KeyboardInterrupt:
    clear_screen()
```

`KeyboardInterrupt` is the `[ON]` key, which is how you break out of a loop
(unverified: read from that app).

**Evidence.** The name and the module-level code are read from published
apps that run on a G2. The lone `start.py` was measured on the Virtual Calculator 2.4, build 2025-09-15, on
2026-10-04: an app built by `hpprime build` from that one file, whose
wrappers are the same template for every app and name no file, drew the
line the file draws when it runs and set the PPL global `PZ` to
`"ZPYENT start.py ran"`, which Home then showed; its Numeric view showed
`>import start`.

<a name="apps.install"></a>
## An app is installed by dragging the folder, never by copying into the mirror

| | |
|---|---|
| Identifier | `apps.install` |
| Kind | rule |
| Known from | G2 |

Open the Connectivity Kit with the calculator connected, or with the Virtual
Calculator running; drag the `.hpappdir` folder from the file manager onto the
calculator in the CK window; then `[Apps]` → your app. Copying it into
`Documents\HP Connectivity Kit\Calculators\<calculator>\` does not work: that
folder is a mirror the CK writes *from* the calculator, and on connecting it
overwrites the folder and your copy disappears. If the drag shows the no-entry
cursor, check whether the CK is set to run as administrator. Both cases, with
the evidence, are in [deploy.md](deploy.md).

Once installed, moving it to another calculator is a drag inside the CK, from
one to the other. The Prime also supports direct calculator-to-calculator
transfer over USB OTG.

**Evidence.** Measured on a G2 with firmware 2.4.15515, and on the Virtual
Calculator, where the folder *is* a mailbox.

<a name="apps.generated-and-verified"></a>
## What has been verified about an app built from the PC

| | |
|---|---|
| Identifier | `apps.generated-and-verified` |
| Kind | rule |
| Known from | G2 |

| | |
|---|---|
| The generated `.hpappprgm` reads back as the same source | yes, and the tool checks it before writing |
| A program generated from Python runs on an HP Prime | yes |
| The Python app wrappers start it in its own screen | yes: they come from an app that runs on this calculator |
| A PPL app assembled end to end by the builder | yes, on a G2: it appears under `[Apps]`, `START()` runs, the program inside computes correctly and its accented text is intact |

Before trusting any result obtained on the calculator, pull the source back
out and compare it with the repository, which is how you find out that the
installed app has been two commits behind the code you were trusting.

**Evidence.** The app used is `examples/apptest/`,
built by `hpprime build --ppl` and run on a G2 with firmware 2.4.15515.

<a name="apps.hpapp-not-generated"></a>
## A .hpapp is copied, not generated

| | |
|---|---|
| Identifier | `apps.hpapp-not-generated` |
| Kind | rule |
| Known from | unverified |

Its internal grammar is not decoded beyond the view byte, and it does not need
to be: it carries no name inside, so one works for all.

**Evidence.** None beyond
[apps.startup-view-byte](#apps.startup-view-byte). Nobody has needed to build
one from nothing.

<a name="apps.empty-hpappprgm-not-a-template"></a>
## The empty .hpappprgm cannot act as a template

| | |
|---|---|
| Identifier | `apps.empty-hpappprgm-not-a-template` |
| Kind | rule |
| Known from | G2 |

It has no source block to replace, and the tool says so: *"no source block
found (empty program?)"*. Use `templates/code.hpprgm`, which ships with the tools. An
app coming back from the calculator can also carry a couple of kilobytes of
compiled block before its source; it reads fine, and it is no use as a
template either
([formats.source-offset-152](formats.md#formats.source-offset-152)).

**Evidence.** Measured on the shipped wrappers and on apps pulled back from a
G2 with firmware 2.4.15515.

<a name="apps.function-needs-active-app"></a>
## An app's functions answer only while its app is active

| | |
|---|---|
| Identifier | `apps.function-needs-active-app` |
| Kind | rule |
| Known from | G2 |

A command belonging to an app is refused from Home when another app is
active, and answers from Home once its own app has been selected. The command
does not have to be typed inside the app: selecting the app is enough, and
the call can then be made from Home as usual. Written with its app's name in
front, a name answers without its app being active (emulator), [apps.qualified-names](#apps.qualified-names).

This is what separates the app functions that a batch can measure from the
ones it cannot. A batch runs on a calculator reset before it, with whatever
app that leaves active, so every command belonging to some other app refuses.

**Evidence.** Measured on a G2 with firmware 2.4.15515. From Home with the
app not active, `SSS(3,4,5)` and `SUM({1,2,3})` are refused. Selecting the
Triangle Solver and then typing `SSS(3,4,5)` on Home answers
`{36.8698976458,53.1301023542,90}`; selecting the Spreadsheet and typing
`SUM({1,2,3})` on Home answers 6. The same holds for the Function app:
`ROOT(F1,1)` answers 2 once `F1` has been given `X^2-4` in the app itself.
One command does not follow it: `Solve2×2` is a syntax error even with
the Linear Solver active.

**It holds inside a program as well, which a batch showed** (emulator). With
the Spreadsheet selected before `HPKDOC` was run, `AVERAGE({2,4,6})` answered
4 and `CellHasData` and `ClearCell` answered 0, where the same three calls
had been refused from a batch with another app active. So the harness can
measure an app's functions, provided a person selects the app first: it
cannot do that itself, because it resets the calculator before every run. Or
the call carries the app's name, which needs nobody, [apps.qualified-names](#apps.qualified-names).

**Being active is necessary and not sufficient.** Only four of the
Spreadsheet's twenty-two names answer even then. The rest want something the
app does not have on a calculator reset before the run -- data in its cells
-- or belong to another app: twelve of them sit in the Inference app's menu
as well, and which app they follow is untested.

**For variables it holds app by app, and inside one app name by name**
(emulator). The Triangle Solver's variables refuse with another app active,
and so do the Function app's. The Finance app splits three ways: with the
Function app active, 50 of its 68 variables answered; nine more -- `NbPmt`,
`IPYR`, `PV`, `PMT`, `FV`, `PPYR`, `CPYR`, `BEG` and `GSize` -- refused and
then answered once Finance was selected; the last nine refused either way.
The Inference app's six lists answered from a foreign app while its `Alpha`
did not. So whether a variable needs its app is a fact about that variable,
and each entry states it rather than inheriting it from the rule.

<a name="apps.qualified-names"></a>
## An app's name in front reaches its variables and functions from another app

| | |
|---|---|
| Identifier | `apps.qualified-names` |
| Kind | rule |
| Known from | emulator |

A program reaches a variable or a function of an app that is not active by
writing the app's name in front of it with a dot, and an underscore where the
app's name has a space: `Statistics_1Var.MeanX`,
`Triangle_Solver.SSS(3,4,5)`. The bare name is refused in the same place,
[apps.function-needs-active-app](#apps.function-needs-active-app). It works
in a program's source as well as through `EXPR`, and it assigns as well as
reads, where the variable takes an assignment at all.

The name in front picks the app: `Statistics_1Var.MeanX` and
`Statistics_2Var.MeanX` are two values. Two things it does not change. The
active app's settings still apply: `Triangle_Solver.SSS(3,4,5)` answers in
radians from the Function app, where the Triangle Solver, active, answers in
degrees, [apps.triangle-solver-degrees](#apps.triangle-solver-degrees). And a
name refused for another reason is still refused: `Solve.Solve`, and the
Statistics 2Var results before the app has data.

It was measured with the Function app active. Whether it works the same with
another app active was not tried (unverified).

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, on
2026-09-25, in two batches with the Function app active
([results.tsv](../commands/results.tsv)). Four controls whose bare form was on
file: `Function.Xmin` answered −15.9, as `Xmin` does, and
`Triangle_Solver.AngleA`, `Inference.Alpha` and `Finance.PV` answered −1,
0.05 and 0, where `AngleA`, `Alpha` and `PV` had been refused under the same
condition. Of the 42 variables of seven apps, every bare name was refused;
with the app's name in front, 28 answered at once and the other 14 once their
app had data or, for `SOLVE`, when called. Twelve took an assignment and read
it back, and 28 refused one. `Do1VStats`, `Do2VStats`, `SUM`, `SSS` and
`SOLVE` answered with the app's name in front, and all five had been refused
bare. Two programs with the form in their source, `ZQREAD`, returning
`Triangle_Solver.AngleA`, and `ZQSTAT`, setting `Statistics_1Var.D1`, running
`Do1VStats` and returning `MeanX`, compiled beside a control program that
compiled and one that did not, and answered −1 and 3.

<a name="apps.triangle-solver-degrees"></a>
## The Triangle Solver answers in degrees while it is active

| | |
|---|---|
| Identifier | `apps.triangle-solver-degrees` |
| Kind | rule |
| Known from | G2 |

While it is the active app its answers are in degrees, where everything
else this documentation has measured is in radians. A program mixing the two gets plausible numbers that
are wrong by a factor of about 57, and nothing raises.

**Evidence.** Measured on a G2 with firmware 2.4.15515: `SSS(3,4,5)` answers
`{36.8698976458,53.1301023542,90}`. Those are the angles of that triangle in
degrees to ten figures, and they sum to 180. In radians they would be
0.6435, 0.9273 and 1.5708, summing to pi. Elsewhere the mode is radians:
`HAngle` answers 0 beside three inverse trigonometric answers,
`angle` of two axes answers half of pi, and `rotation` writes a turn of one
radian as an exponential.

**Called with its app's name in front from another app, it answers in
radians** (emulator): with the Function app active,
`Triangle_Solver.SSS(3,4,5)` answered
`{0.643501108793,0.927295218002,1.57079632679}`, the same angles in radians.
So the unit follows the app that is active, not the app the command belongs
to, as [apps.app-mode-overrides-home](#apps.app-mode-overrides-home) found for
Home's settings, and a program calling the Triangle Solver that way gets
radians, [apps.qualified-names](#apps.qualified-names).

<a name="apps.reset-leaves-function-active"></a>
## A reset calculator has the Function app active

| | |
|---|---|
| Identifier | `apps.reset-leaves-function-active` |
| Kind | rule |
| Known from | emulator |

There is no state on the Prime in which no app is active, so "with no app
open" is not a condition a measurement can have. The harness resets its calculator
before every run, and what that leaves active is the **Function** app. Every
batch that nobody has touched first therefore measures the Function-app
condition, not a neutral one.

**Evidence.** Two batches, differing only in what a person selected first.
With nothing selected, the Function app's variables answered -- `Root`,
`Slope` and `SignedArea` all 0 -- while the Triangle Solver's refused. With
the Triangle Solver selected and nothing else changed, that reversed
exactly: `AngleA`, `AngleB`, `AngleC`, `SideA`, `SideB` and `SideC` all
answered −1 and `TriType` 0, and `Root` was refused. A name cannot stop
working because another app was chosen unless the first app was the thing
making it work.

**What it changes.** Every `emulator` row in this documentation taken from an
untouched batch was measured with the Function app active. For names outside
that app this is the same as the app not being active, which is how those
rows were read and why the reading still stands. For the five Function app
commands and the five Function app variables it is not: their rows record an
app that happened to be open, and any of them saying otherwise is wrong.

**One variable answers under both conditions and is not explained by this**
(emulator): `Xlist`, of the Inference app, answered `{}` with the Function
app active and again with the Triangle Solver active. Whether any other
variable behaves that way is untested.


<a name="apps.app-mode-overrides-home"></a>
## The active app's mode overrides Home's

| | |
|---|---|
| Identifier | `apps.app-mode-overrides-home` |
| Kind | rule |
| Known from | emulator |

A program run from Home computes, and writes numbers as text, in the mode of
the active app wherever that app's setting is not 0, whatever Home's says:

| The app's setting | Set to | A program on Home, with Home's at its reset value |
|---|---|---|
| [AAngle](../commands/common-app-mode/AAngle.md) | 2 | `SIN(90)` answers 1: degrees |
| [AComplex](../commands/common-app-mode/AComplex.md) | 2 | `(-4)^0.5` answers `2*i`, where Home refuses it |
| [AFormat](../commands/common-app-mode/AFormat.md) | 2 | `STRING(1/3)` answers `"0.3333"`, as many decimals as [ADigits](../commands/common-app-mode/ADigits.md) |

At 0, each leaves the choice to Home's own
[HAngle](../commands/home-settings/HAngle.md),
[HComplex](../commands/home-settings/HComplex.md) and
[HFormat](../commands/home-settings/HFormat.md). The app's values are
shifted by one against Home's: its own choices start at 1, so `AAngle` 1 is
radians where `HAngle` 0 is.

So the same program answers differently depending on which app is active and
how it is set. The Triangle Solver's degrees,
[apps.triangle-solver-degrees](#apps.triangle-solver-degrees), and the
Finance app's two decimals,
[apps.finance-shows-two-decimals](#apps.finance-shows-two-decimals), are
likely this rule with those apps' own settings, which were not read
(unverified).

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, on
2026-09-24, with the Function app active, as on a reset calculator, each
setting changed and put back inside one row
([results.tsv](../commands/results.tsv)). `AAngle` at 1 made `SIN(90)`
answer 0.893996663601, the sine of 90 radians, and at 0 the same; `AComplex`
and `AFormat` at 1 changed nothing. Another app was not tried.

<a name="apps.finance-shows-two-decimals"></a>
## The Finance app turns numbers into text with two decimals

| | |
|---|---|
| Identifier | `apps.finance-shows-two-decimals` |
| Kind | rule |
| Known from | emulator |

While the Finance app is active, a real becomes text with two decimals: 12
comes out as `12.00` and 0 as `0.00`. The number is unchanged; its text is
not. A program that builds a message, a file or a comparison out of `STRING`
gets a different string depending on which app happens to be active.

**Evidence.** The harness makes every answer's text with `STRING` on the
calculator itself. Three Finance variables were read in two batches that
differed only in the app selected first: with the Function app active
`CFPYR`, `BSCall` and `TotalCF` came back `12`, `0` and `0`; with Finance
active, `12.00`, `0.00` and `0.00`. No other app measured in this
documentation has done it: the Triangle Solver answered `36.8698976458`, the
Inference app `0.461368`.

**What it changes here.** Every `emulator` row taken with Finance active
carries two decimals, and those rows are correct as the calculator displayed
them. An entry quoting one says why, so the decimals are not read as part of
the value.

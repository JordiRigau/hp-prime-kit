# The tools

Every command in one place. Python 3.7 or newer, no dependencies, nothing to
install.

```bash
hpprime <command> [arguments]
```

Run it from the repository folder. How you type `hpprime` depends on your
shell: `.\hpprime` in PowerShell (the `.\` is required), `hpprime` in
cmd.exe, `./hpprime` on macOS and Linux. `python hpprime.py` works
everywhere and is the one to fall back on.

Every command exits **0 on success and non-zero on failure**, so they all
work as gates in a script.

---

## doctor

```bash
hpprime doctor
```

Says what works on this machine: Python version, whether the code template
and the app templates are there and valid, whether a Connectivity Kit folder
exists, and an end-to-end self test (source → `.hpprgm` → source, and the PPL
runs). Anything wrong comes with what to do about it.

Run it first, and again whenever something behaves strangely.

## new

```bash
hpprime new NAME              # a PPL program: NAME.txt
hpprime new NAME --python     # a Python app: NAME/main.py
```

Writes a starter that already compiles and runs, and prints the commands to
take it to the calculator. The name is what it will be called there: letters
and digits, no spaces.

## lint

```bash
hpprime lint FILE.txt
hpprime lint ppl/ --quiet          # errors only, no warnings
hpprime lint A.txt B.txt --set     # also: names that would collide
```

Catches, before you compile, what the Prime's compiler will not explain.
Output is compiler-shaped -- `file:line: level: rule: message` -- and it
exits 1 if there is any error.

Twelve rules, each from an error measured on a G2: too many variables in one
`LOCAL` (`local-limit`), indexing the result of a call (`index-call`),
`ENDIF` and friends (`single-end`), comparing with `=` (`equality`), index 0
(`one-based`), a `LOCAL` after code (`local-first`), several initialised
variables in one `EXPORT` (`export-multiple`), a function's `END` without its
semicolon (`end-semicolon`), unclosed blocks (`unbalanced`), `EXPR` without a
guard (`expr-empty`), duplicate exported names (`export-clash`, with
`--set`), and `TEXTOUT_P` without its width (`textout-width`).

`local-limit`, `expr-empty` and `textout-width` are warnings: the code
compiles and runs, and what they flag is a hazard, not a mistake. Everything
else is an error and exits 1.

Just as important is what it does **not** flag. `RETURN` inside a `FOR` is
legal; locals like `L12` or `r2` are legal; several locals with initial
values on one line are legal. Those were each checked on hardware and are
listed in the source so nobody "fixes" them back in.

`--set` is for files that go to the calculator together: it adds a check for
exported names that would collide as globals.

## run

```bash
hpprime run FILE.txt --call "AREA(2)"
hpprime run lib.txt data.txt --call "LOAD(1)" --call "F(3,350)"
```

Runs the PPL, on your PC. Not a reimplementation: the same file you install.

From Python:

```python
from hpkit import interp
m = interp.Machine()
m.load_file('ppl/LIB.hpprgm')
r = m.call('F', 3.0, 350.0)
```

**What it covers**: numbers, strings, lists, **1-based** matrices,
`IF`/`CASE`/`FOR`/`WHILE`/`REPEAT`/`IFERR`, `EXPORT` functions, globals and
locals, matrices passed **by value**, and the native matrix algebra --
`MAKEMAT`, `MAKELIST`, `RREF`, `TRN`, `DET`, `INVERSE`, `IDENMAT`.

**What it records instead of drawing**: `TEXTOUT_P`, `RECT`, `INPUT`,
`CHOOSE`, `WAIT`, `MSGBOX`. Each goes into `machine.io` and returns a neutral
value, so a program with an interface still runs end to end.

**What it does not cover raises.** Never an invented result. If you need a
command, add it to `BUILTINS` with its case in `tests/test_interp.py` -- and
measure it on the calculator first.

Deliberately still missing: the string functions (`LEFT`, `MID`, `INSTRING`,
`SORT`…). Their edge behaviour is not measured here, and a guessed semantics
would return a number where the calculator returns another -- exactly the
divergence this exists to catch.

One fidelity gap worth knowing: `M := GZ` (assigning a global matrix to a
local) **aliases here and copies on the Prime**. The way never to be bitten
is not to do it: work on the global.

## write / read / verify

```bash
hpprime write source.txt -o PROG.hpprgm     # build the binary
hpprime read PROG.hpprgm -o source.txt      # pull the source back out
hpprime verify PROG.hpprgm                  # round-trip check
hpprime verify MYAPP.hpappdir *.py          # app folder check
```

`write` uses `templates/code.hpprgm`, which the kit ships, unless you pass
`-t`. It reads back what it wrote before reporting success, and it refuses a
template that carries a compiled block, because changing the source would
leave that block out of step.

`read` works on anything with the container's magic, including the
`.hpappprgm` inside an app. Use it to compare what is installed with your
repository:

```bash
hpprime read ".../Calculators/HP Prime/MYPROG.hpprgm" -o installed.txt
diff installed.txt ppl/MYPROG.txt
```

`verify` takes either a `.hpprgm` (rebuilds it and compares) or an app folder
(compares it with what a build would produce, which is how you catch the
calculator having rewritten the wrappers).

It works out which kind of app it is looking at, because the two are not
compared the same way: a PPL app is built from the blank descriptor and its
`.hpappprgm` is *supposed* to differ from the empty skeleton. Give it the
sources too and it checks those as well -- otherwise it says which parts it
did not compare:

```bash
hpprime verify MYAPP.hpappdir src/*.py     # a Python app
hpprime verify MYAPP.hpappdir app.txt      # a PPL app, program included
```

## build

```bash
hpprime build MYAPP src/*.py --icon icon.png   # a Python app
hpprime build MYAPP app.txt --ppl              # a PPL app
```

Builds a `.hpappdir`: the three wrappers, plus your files. The wrappers are
rebuilt from the templates every time, on purpose -- the calculator rewrites
them when you leave the app, and that state must not survive into your
repository.

It also deletes `__pycache__` (CPython `.pyc` files MicroPython would not
read), warns if a Python app has no `main.py`, and warns about imports
MicroPython does not have -- which on the calculator show up as the app
closing at startup, silently. `--allow a,b` for modules you know are there.

## matrix

```bash
hpprime matrix read  M1.hpmat -o data.csv
hpprime matrix write data.csv -o M0.hpmat
hpprime matrix nums  PROG.hpprgm
```

`.hpmat` files are the `M0`..`M9` matrices, and the file name decides which
one. This lets a whole matrix reach the calculator **as a file**, with
nothing pasted.

`nums` looks inside a program's compiled block and reports the matrices it
recognises. For looking, not for rewriting: generating that block is not
solved. See [formats.md](reference/formats.md).

Complex matrices raise an explicit error rather than returning invented
numbers.

## templates

```bash
hpprime templates "C:\Users\you\Documents\HP Connectivity Kit\Calculators"
```

Says which of your `.hpprgm` files can act as a template for `write`. You
need this only if the shipped template ever fails you -- and it is not
obvious by eye, because the mirror folder holds files that have been through
the calculator, which adds a compiled block to everything it saves. Measured
on one machine: 2 of 58 qualified.

---

## Testing the kit itself

```bash
python tests/run_all.py
```

Eight suites, and none of them needs a calculator. Two of them use one if it
is there: the `.hpprgm` reader against your own binaries, and the number
format against your own data. They skip what they cannot find rather than
failing.

| Suite | What it covers |
|---|---|
| `test_lint.py` | that the linter catches, and that it does not raise false alarms |
| `test_interp.py` | the interpreter's subset, and that it fails where it must |
| `test_program.py` | the shipped template, and round trips over your binaries |
| `test_appdir.py` | building an app, and what `verify` sees |
| `test_numbers.py` | the internal number format, against real encodings |
| `test_cli.py` | the whole `hpprime` path a newcomer walks |
| `test_examples.py` | the starters and examples, so the first thing anybody copies still works |
| `test_docs.py` | every relative link in the documentation resolves |

## Using the modules directly

Every command is a thin front over a module you can import:

```python
from hpkit import lint, interp, program, appdir, numbers
```

| Module | Main entry points |
|---|---|
| `lint` | `check_source(path, text)`, `check_files(paths)` |
| `interp` | `Machine()`, `.load_file()`, `.call()`, `.io` |
| `program` | `read(data)`, `write(template, source)`, `default_template()` |
| `appdir` | `build()`, `check()`, `put_ppl_program()`, `check_imports()` |
| `numbers` | `decode()`, `encode()`, `read_hpmat()`, `write_hpmat()` |

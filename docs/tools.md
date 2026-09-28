# The tools

Every command in one place. Python 3.7 or newer, no dependencies, nothing to
install.

```bash
hpprime <command> [arguments]
```

Run it from the repository folder. How you type `hpprime` depends on your
shell: `.\hpprime` in PowerShell, where the `.\` is required, `hpprime` in
cmd.exe, and `./hpprime` on macOS and Linux. `python hpprime.py` works
everywhere and is the one to fall back on.

Every command exits 0 on success and non-zero on failure, so they all work as
gates in a script.

---

## doctor

```bash
hpprime doctor
```

Reports what works on this machine: the Python version, whether the code
template and the app templates are there and valid, whether a Connectivity Kit
folder exists, where the emulator is and which calculators it has, whether it
is running, which `install` cares about, and an end-to-end self test (source →
`.hpprgm` → source, and the PPL runs). Anything wrong comes with what to do
about it.

Run it first, and again whenever something behaves strangely.

## new

```bash
hpprime new NAME              # a PPL program: programs/NAME/NAME.txt
hpprime new NAME --python     # a Python app: programs/NAME/main.py
hpprime new NAME -o DIR       # somewhere else: DIR/NAME.txt
```

Writes a starter that already compiles and runs, in a folder of its own under
`programs/`, and prints the commands to take it to the calculator, with its
paths. Git ignores what is in `programs/`, so what you make there stays yours.
The name is what it will be called on the calculator: letters and digits, no
spaces.

## update

```bash
hpprime update                     # to the latest version on GitHub
hpprime update --from main.zip     # to a ZIP you downloaded yourself
hpprime update --dry-run           # say what would change, write nothing
```

Brings a downloaded copy of the repository up to date: it fetches the `main`
branch as a ZIP and writes the files that changed and the new ones. A clone
updates with `git pull`, and this refuses to run in one.

It never writes inside `programs/`, nor to `.claude/settings.local.json`, and
it never deletes. A file on disk that the new version no longer has is listed
for you to remove, since it could be yours; files the repository's
`.gitignore` marks, such as built `.hpprgm` files, are not listed. It says how
many files changed, and which commit it installed.

If the download fails, download the ZIP by hand (on GitHub, **Code**, then
**Download ZIP**) and pass it with `--from`.

## lint

```bash
hpprime lint FILE.txt
hpprime lint ppl/ --quiet          # errors only, no warnings
hpprime lint A.txt B.txt --set     # also: names that would collide
```

Catches, before you compile, what the Prime's compiler will not explain. The
output is compiler-shaped, `file:line: level: rule: message [fact, label]`,
and it exits 1 if there is any error. What is in brackets is the identifier
of the fact the rule comes from, so a message can be checked rather than
believed, and how that finding is known, in [format.md](format.md)'s words.

```
prog.txt:5: ERROR: index-call: cannot index the result of a call (SIZE(...)(...)): store it first, d := DIM(M); d(1) [ppl.index-call, G2]
prog.txt:9: WARN: one-based: index 0 into L: positions count from 1. A list read at 0 answers its LAST element and one assigned at 0 grows by one; a matrix read at 0 is an error [ppl.one-based, emulator]
```

A rule is an error only as far as its measurement reaches. What was measured
for `index-call` is a call indexed where it is produced -- `SIZE(M)(1)`, and a
program's own function, in its file or another -- so that is an error; a
name the file does not define, which may be a function or a list, is a
warning, since the file cannot say which; and a list indexed twice,
`L(2)(1)`, is not flagged at all. The same split runs through the rest.
`local-limit` is an error from 9 variables and a warning at 7 and 8, which
compile. `export-multiple` is an error from 7 initialised variables, and 2 to
6 are not flagged, since all five compiled. `local-first` is an error for a
`LOCAL` half way down a function; one inside a nested block compiles and is
not flagged. `end-semicolon` is an error for a block's `END` and for a
function's own. `single-end` is an error for `ENDIF`, `ENDFOR`, `ENDWHILE`,
`ENDCASE`, `ENDFUNC` and `ENDPROC`, none of which compiled. `one-based` is a warning,
labelled `emulator`: a list read at 0 does not fail, it answers its last
element, which is the hazard for anybody expecting the first, and a matrix
read at 0 does fail. The linter cannot tell a list from a matrix by its
name, so it warns on both. A 0 passed to a function the file defines is an
argument, and is not flagged. When somebody measures one of these cases, it
becomes an error with its evidence. `tests/test_lint.py` fails on an error
whose label is not `G2` or `emulator`.

Twenty rules, and each one says where it comes from. Eighteen name a fact in
[docs/topics/](topics/ppl.md), every one of them measured on a G2 or on the
emulator: too many variables in one `LOCAL` (`local-limit`), indexing the
result of a call (`index-call`), `ENDIF` and friends (`single-end`), index 0
(`one-based`), a `LOCAL` after code (`local-first`), several initialised
variables in one `EXPORT` (`export-multiple`), an `END` without its semicolon
(`end-semicolon`), `EXPR` without a guard (`expr-empty`), duplicate exported
names (`export-clash`, with `--set`), `TEXTOUT_P` without its width
(`textout-width`), a single `=` as a statement (`equality-statement`), and
the seven below.

A rule called `equality` once flagged a single `=` in a condition as an
error, and on 2026-09-12 the calculator settled it: `IF a = 2 THEN` compiles
and compares, exactly as `==` does. The rule was removed rather than softened,
because a linter that flags legal, correct code is worse than one rule short.
As a statement it is another matter, measured on 2026-09-24: `za = 2;`
compiles and assigns nothing. `equality-statement` warns on that, and only
on a line that starts with the name, so a condition is never flagged.
`ppl.equality-operators` holds both measurements.

Seven came from the table below, of what catches each fact, and one rule
grew. `mu-zero` is an error: `μ₀` spelled as HP's list spells it, with the
Greek mu, does not compile, and with the micro sign it does. The rest warn on
code that runs and does something other than what it looks like: a key's
code from `GETKEY` compared with text or with a number no key has
(`getkey-code`); a string's element compared with a string, when it is a
character's code and never equal (`string-index`); a drawing command without
`_P` given coordinates in pixels (`draw-units`); an exported program that
draws and nowhere waits, whose drawing is gone when it returns
(`draw-then-return`); a loop waiting for a key with nothing drained first
(`wait-undrained`); and `EXPR` inside a loop (`expr-in-loop`).
`export-clash` also warns, without `--set`, on an export named like one of
HP's own, which hides it: a program exporting `AREA` hides the Function
app's. The rules that read a whole function follow the file's own calls,
and leave alone a function that calls a name no file in view defines.

`unbalanced` names no fact, because an unclosed block is something the
compiler reports itself and no fact about the platform is involved.

The last, `unknown-name`, knows every PPL name. A call to a name that is
not on the documentation's [list of names](commands/names.tsv), and that the
program does not define, is flagged: the command a model invents, `STRLEN(s)`
for `SIZE(s)`, caught before the calculator answers *syntax error*. It knows
the calculator's own variables too (`A` to `Z`, `L0` to `L9`, `M0` to `M9`,
`G0` to `G9`, `Z0` to `Z9`), and it compares the calculator's names without
regard to case, so that it never flags a spelling the calculator accepts:
the calculator reads a command's name in any case,
[ppl.names-ignore-case](topics/ppl.md#ppl.names-ignore-case).
It names no fact either: it comes from the list of names, which is an
inventory rather than something measured about the platform.
`tests/test_lint.py` fails if any rule names a fact no topic page defines, or
names none and gives no reason.

Every warning carries a measured fact: the code compiles and runs, and what
it flags is a hazard rather than a mistake. `unknown-name` is a warning for a
file on its own, because the file may be calling a function
that another program exports, and an error with `--set`. Every other finding
is an error, and only an error exits 1. `--quiet` hides the warnings.

What it does not flag matters as much. `RETURN` inside a `FOR` is legal; locals
like `L12` or `r2` are legal; several locals with initial values on one line
are legal. Each was checked on hardware, and they are listed in the source so
that nobody puts the false rule back.

`--set` is for files that go to the calculator together: it adds a check for
exported names that would collide as globals, and it makes `unknown-name` an
error, because with every file in view nothing else could supply the name.

### What catches each fact

Every fact in the topic pages has a line here: the lint rule that catches it,
another command and the test that holds it, nothing to catch where the
mistake would be to flag it, or why nothing on a PC can see it.
`tests/test_lint.py` fails if a fact has no line, or a line names a rule or a
test that is not there.

<!-- Written by `hpprime docs` from CAUGHT in hpkit/lint.py, which is where it is edited. -->
| Fact | Known from | Caught by |
|---|---|---|
| [apps.hpappdir-contents](topics/apps.md#apps.hpappdir-contents) | G2 | `hpprime build`, held by `test_appdir.py` |
| [apps.startup-view-byte](topics/apps.md#apps.startup-view-byte) | G2 | `hpprime verify`, held by `test_appdir.py` |
| [apps.icon](topics/apps.md#apps.icon) | G2 | not from a PC: what another size does was not measured, so none can be called wrong |
| [apps.two-kinds](topics/apps.md#apps.two-kinds) | G2 | `hpprime verify`, held by `test_appdir.py` |
| [apps.hooks](topics/apps.md#apps.hooks) | G2 | not from a PC: a hook is an exported function like any other, so a file cannot say which ones were meant as hooks |
| [apps.blank-app-hooks](topics/apps.md#apps.blank-app-hooks) | G2 | not from a PC: it is what the calculator does with an app's views while its program runs |
| [apps.blank-app-keys](topics/apps.md#apps.blank-app-keys) | G2 | not from a PC: which keys arrive is known only while the program runs |
| [apps.exports-tied](topics/apps.md#apps.exports-tied) | G2 | not from a PC: where a program is installed, in an app or in the catalogue, is not in its file |
| [apps.wrappers-are-portable](topics/apps.md#apps.wrappers-are-portable) | G2 | `hpprime build`, held by `test_appdir.py` |
| [apps.main-py](topics/apps.md#apps.main-py) | unverified | `hpprime build`, held by `test_appdir.py` |
| [apps.install](topics/apps.md#apps.install) | G2 | `hpprime install`, held by `test_emulator.py`; not from a PC: on a physical calculator it is a person dragging the folder in the Connectivity Kit |
| [apps.generated-and-verified](topics/apps.md#apps.generated-and-verified) | G2 | `hpprime verify`, held by `test_appdir.py` |
| [apps.hpapp-not-generated](topics/apps.md#apps.hpapp-not-generated) | unverified | `hpprime build`, held by `test_appdir.py` |
| [apps.empty-hpappprgm-not-a-template](topics/apps.md#apps.empty-hpappprgm-not-a-template) | G2 | `hpprime build`, held by `test_appdir.py` |
| [apps.function-needs-active-app](topics/apps.md#apps.function-needs-active-app) | G2 | not from a PC: which app is active is the calculator's state, not the file's |
| [apps.qualified-names](topics/apps.md#apps.qualified-names) | emulator | nothing to catch, and `lint` stays quiet; `hpprime run`, held by `test_interp.py` |
| [apps.triangle-solver-degrees](topics/apps.md#apps.triangle-solver-degrees) | G2 | not from a PC: which app is active is the calculator's state, not the file's |
| [apps.reset-leaves-function-active](topics/apps.md#apps.reset-leaves-function-active) | emulator | not from a PC: it is the state a reset leaves on the calculator |
| [apps.app-mode-overrides-home](topics/apps.md#apps.app-mode-overrides-home) | emulator | not from a PC: which app is active is the calculator's state, not the file's |
| [apps.finance-shows-two-decimals](topics/apps.md#apps.finance-shows-two-decimals) | emulator | not from a PC: which app is active is the calculator's state, not the file's |
| [deploy.emulator-folder](topics/deploy.md#deploy.emulator-folder) | emulator | `hpprime install`, held by `test_emulator.py` |
| [deploy.compile-once-after-a-file-copy](topics/deploy.md#deploy.compile-once-after-a-file-copy) | emulator | not from a PC: Check is a key pressed on the calculator: the tools say when to press it and cannot press it |
| [deploy.results-come-back-on-exit](topics/deploy.md#deploy.results-come-back-on-exit) | emulator | `hpprime compare`, held by `test_compare.py` |
| [deploy.which-window-opens](topics/deploy.md#deploy.which-window-opens) | emulator | `hpprime examples`, held by `test_examples_run.py` |
| [deploy.calc-hpsettings-moves](topics/deploy.md#deploy.calc-hpsettings-moves) | emulator | `hpprime examples`, held by `test_examples_run.py` |
| [deploy.ck-mirror](topics/deploy.md#deploy.ck-mirror) | G2 | not from a PC: installing on a physical calculator is a person dragging the file in the Connectivity Kit |
| [deploy.content-library-send](topics/deploy.md#deploy.content-library-send) | G2 | not from a PC: it is a person's action in the Connectivity Kit or on the calculator |
| [deploy.usb-without-the-ck](topics/deploy.md#deploy.usb-without-the-ck) | unverified | not from a PC: it is a route nobody has, so there is nothing to check |
| [deploy.drag-refused-when-elevated](topics/deploy.md#deploy.drag-refused-when-elevated) | G2 | not from a PC: it is Windows' settings for the Connectivity Kit |
| [deploy.no-manual-compile](topics/deploy.md#deploy.no-manual-compile) | G2 | not from a PC: it is what a physical calculator does with a file it receives |
| [deploy.read-it-back](topics/deploy.md#deploy.read-it-back) | G2 | `hpprime pull`, held by `test_emulator.py` |
| [deploy.writer-on-hardware](topics/deploy.md#deploy.writer-on-hardware) | G2 | `hpprime write`, held by `test_cli.py`; not from a PC: that it runs on a G2 is for the hardware to say |
| [deploy.template-from-the-ck](topics/deploy.md#deploy.template-from-the-ck) | G2 | `hpprime write`, held by `test_program.py` |
| [deploy.which-calculator-is-which](topics/deploy.md#deploy.which-calculator-is-which) | G2 | `hpprime emu`, held by `test_emulator.py` |
| [formats.container](topics/formats.md#formats.container) | G2 | `hpprime write`, held by `test_program.py` |
| [formats.source-record](topics/formats.md#formats.source-record) | G2 | `hpprime read`, held by `test_program.py` |
| [formats.wrapper-trap](topics/formats.md#formats.wrapper-trap) | G2 | `hpprime read`, held by `test_program.py` |
| [formats.trailer-varies](topics/formats.md#formats.trailer-varies) | G2 | `hpprime write`, held by `test_program.py` |
| [formats.header-words](topics/formats.md#formats.header-words) | unverified | not from a PC: what the two words mean is not known, so no value can be called wrong |
| [formats.line-endings](topics/formats.md#formats.line-endings) | G2 | `hpprime write`, held by `test_cli.py` |
| [formats.source-offset-152](topics/formats.md#formats.source-offset-152) | G2 | `hpprime write`, held by `test_program.py` |
| [formats.two-producers](topics/formats.md#formats.two-producers) | G2 | `hpprime write`, held by `test_program.py` |
| [formats.block-is-a-cache](topics/formats.md#formats.block-is-a-cache) | G2 | not from a PC: the calculator builds the block, and nothing on the PC writes one |
| [formats.block-not-byte-stable](topics/formats.md#formats.block-not-byte-stable) | G2 | not from a PC: it is about two compiles on the calculator, and no tool compares blocks |
| [formats.number](topics/formats.md#formats.number) | G2 | `hpprime matrix`, held by `test_numbers.py` |
| [formats.number-infinity](topics/formats.md#formats.number-infinity) | emulator | `hpprime matrix`, held by `test_numbers.py` |
| [formats.hpmat](topics/formats.md#formats.hpmat) | G2 | `hpprime matrix`, held by `test_numbers.py` |
| [formats.hpmat-vector](topics/formats.md#formats.hpmat-vector) | emulator | `hpprime matrix`, held by `test_numbers.py` |
| [formats.symbol-table](topics/formats.md#formats.symbol-table) | G2 | `hpprime matrix`, held by `test_numbers.py` |
| [formats.matrix-type-byte](topics/formats.md#formats.matrix-type-byte) | G2 | `hpprime matrix`, held by `test_numbers.py` |
| [formats.value-types-undecoded](topics/formats.md#formats.value-types-undecoded) | unverified | not from a PC: they are not decoded, so there is nothing to check a value against |
| [formats.matrix-flag](topics/formats.md#formats.matrix-flag) | unverified | not from a PC: what the flag means is not known |
| [formats.entry-splice](topics/formats.md#formats.entry-splice) | unverified | not from a PC: nothing on the PC writes a symbol entry into a program |
| [formats.other-files](topics/formats.md#formats.other-files) | G2 | `hpprime install`, held by `test_emulator.py` |
| [interface.geometry](topics/interface.md#interface.geometry) | G2 | not from a PC: a coordinate past the edge is clipped, not refused, and a file cannot say it was meant to be seen |
| [interface.draw-units](topics/interface.md#interface.draw-units) | emulator | lint rule `draw-units` |
| [interface.offscreen-grob](topics/interface.md#interface.offscreen-grob) | G2 | not from a PC: drawing straight onto the screen is correct; the flicker is what a person sees |
| [interface.two-themes](topics/interface.md#interface.two-themes) | unverified | not from a PC: it is about what a person sees on the screen |
| [interface.textout-width](topics/interface.md#interface.textout-width) | G2 | lint rule `textout-width` |
| [interface.text-measure](topics/interface.md#interface.text-measure) | unverified | not from a PC: it is about what the calculator answers, which the source does not show |
| [interface.input-fields](topics/interface.md#interface.input-fields) | G2 | not from a PC: it is how a form looks on the screen, and only two label positions were measured |
| [interface.input-modal](topics/interface.md#interface.input-modal) | G2 | not from a PC: it is what a form does while it is open |
| [interface.getkey-position](topics/interface.md#interface.getkey-position) | G2 | lint rule `getkey-code` |
| [interface.key-codes](topics/interface.md#interface.key-codes) | G2 | lint rule `getkey-code` |
| [interface.soft-labels-not-keys](topics/interface.md#interface.soft-labels-not-keys) | G2 | not from a PC: which keys a program gives its labels is a choice, and no code is wrong in itself |
| [interface.draw-then-return](topics/interface.md#interface.draw-then-return) | G2 | lint rule `draw-then-return` |
| [interface.drain-then-wait](topics/interface.md#interface.drain-then-wait) | G2 | lint rule `wait-undrained` |
| [interface.wait-minus-one](topics/interface.md#interface.wait-minus-one) | emulator | not from a PC: it waited on the emulator and once did not on a G2, for a reason not known, so there is no form to flag |
| [interface.mouse-lists](topics/interface.md#interface.mouse-lists) | G2 | `hpprime build`, held by `test_appdir.py` |
| [interface.touch-readings](topics/interface.md#interface.touch-readings) | unverified | not from a PC: it is a finger's movement, which only a running app sees |
| [interface.dialog-touch-twice](topics/interface.md#interface.dialog-touch-twice) | G2 | not from a PC: it is a touch that outlives a dialog, while the app runs |
| [interface.screen-capacity](topics/interface.md#interface.screen-capacity) | unverified | not from a PC: it is about what a person sees on the screen |
| [libraries.published](topics/libraries.md#libraries.published) | unverified | not from a PC: it is about somebody else's code, not run here |
| [libraries.skeletonapp-container](topics/libraries.md#libraries.skeletonapp-container) | unverified | `hpprime install`, held by `test_emulator.py` |
| [libraries.usb-keyboard](topics/libraries.md#libraries.usb-keyboard) | unverified | not from a PC: it is about somebody else's code, not run here |
| [micropython.modules](topics/micropython.md#micropython.modules) | G2 | `hpprime build`, held by `test_appdir.py` |
| [micropython.community-modules](topics/micropython.md#micropython.community-modules) | unverified | not from a PC: nobody here has run them, so none can be called missing |
| [micropython.hpprime-module](topics/micropython.md#micropython.hpprime-module) | G2 | not from a PC: it lists calls that work, and there is nothing in it to get wrong |
| [micropython.hpprime-undocumented](topics/micropython.md#micropython.hpprime-undocumented) | unverified | not from a PC: none of it has been run here |
| [micropython.eval](topics/micropython.md#micropython.eval) | G2 | not from a PC: it says what works across the bridge, and there is nothing in it to get wrong |
| [micropython.eval-parentheses](topics/micropython.md#micropython.eval-parentheses) | unverified | not from a PC: which form is required is not known |
| [micropython.list-with-string-closes-the-app](topics/micropython.md#micropython.list-with-string-closes-the-app) | G2 | `hpprime build`, held by `test_appdir.py`; not from a PC: for any other call, what it returns is known only when it runs |
| [micropython.string-quotes](topics/micropython.md#micropython.string-quotes) | G2 | not from a PC: the quote comes from data at run time |
| [micropython.number-notation](topics/micropython.md#micropython.number-notation) | unverified | not from a PC: the number is written at run time, and the failure has not been reproduced here |
| [micropython.bridge-cost](topics/micropython.md#micropython.bridge-cost) | G2 | not from a PC: it is a time, which only the calculator can take |
| [micropython.imports](topics/micropython.md#micropython.imports) | G2 | `hpprime build`, held by `test_appdir.py` |
| [micropython.mark-debugging](topics/micropython.md#micropython.mark-debugging) | G2 | not from a PC: it is a way of finding a failure, not a mistake |
| [micropython.ppl-calls-python](topics/micropython.md#micropython.ppl-calls-python) | unverified | not from a PC: it has not been measured here |
| [micropython.not-measured](topics/micropython.md#micropython.not-measured) | unverified | not from a PC: it is a list of what has not been measured |
| [ppl.local-limit](topics/ppl.md#ppl.local-limit) | G2 | lint rule `local-limit`; `hpprime run`, held by `test_interp.py` |
| [ppl.locals-at-top](topics/ppl.md#ppl.locals-at-top) | G2 | lint rule `local-first` |
| [ppl.index-call](topics/ppl.md#ppl.index-call) | G2 | lint rule `index-call` |
| [ppl.export-initialised](topics/ppl.md#ppl.export-initialised) | G2 | lint rule `export-multiple`; `hpprime run`, held by `test_interp.py` |
| [ppl.no-end-keywords](topics/ppl.md#ppl.no-end-keywords) | G2 | lint rule `single-end` |
| [ppl.minus-sign](topics/ppl.md#ppl.minus-sign) | emulator | not from a PC: it is about what the calculator answers, which the source does not show |
| [ppl.one-based](topics/ppl.md#ppl.one-based) | G2 | lint rule `one-based`; `hpprime run`, held by `test_interp.py` |
| [ppl.string-index-code](topics/ppl.md#ppl.string-index-code) | emulator | lint rule `string-index`; `hpprime run`, held by `test_interp.py` |
| [ppl.names-ignore-case](topics/ppl.md#ppl.names-ignore-case) | emulator | nothing to catch, and `lint` stays quiet |
| [ppl.equality-operators](topics/ppl.md#ppl.equality-operators) | emulator | lint rule `equality-statement` |
| [ppl.end-semicolon](topics/ppl.md#ppl.end-semicolon) | emulator | lint rule `end-semicolon`; `hpprime run`, held by `test_interp.py` |
| [ppl.global-index-other-program](topics/ppl.md#ppl.global-index-other-program) | G2 | nothing to catch, and `lint` stays quiet |
| [ppl.return-in-loop](topics/ppl.md#ppl.return-in-loop) | G2 | nothing to catch, and `lint` stays quiet |
| [ppl.letter-digit-names](topics/ppl.md#ppl.letter-digit-names) | G2 | nothing to catch, and `lint` stays quiet |
| [ppl.local-m-matrices](topics/ppl.md#ppl.local-m-matrices) | G2 | nothing to catch, and `lint` stays quiet |
| [ppl.locals-initialised-one-line](topics/ppl.md#ppl.locals-initialised-one-line) | emulator | nothing to catch, and `lint` stays quiet |
| [ppl.i-e-as-locals](topics/ppl.md#ppl.i-e-as-locals) | emulator | nothing to catch, and `lint` stays quiet; `hpprime run`, held by `test_interp.py` |
| [ppl.imaginary-unit](topics/ppl.md#ppl.imaginary-unit) | emulator | not from a PC: it is about what the calculator answers, which the source does not show |
| [ppl.exponent-glyph](topics/ppl.md#ppl.exponent-glyph) | emulator | not from a PC: it is about what the calculator answers, which the source does not show |
| [ppl.exact-answers](topics/ppl.md#ppl.exact-answers) | emulator | not from a PC: it is about what the calculator answers, which the source does not show |
| [ppl.type-codes](topics/ppl.md#ppl.type-codes) | emulator | not from a PC: it is about what the calculator answers, which the source does not show |
| [ppl.function-always-answers](topics/ppl.md#ppl.function-always-answers) | G2 | `hpprime run`, held by `test_interp.py` |
| [ppl.home-no-parentheses](topics/ppl.md#ppl.home-no-parentheses) | G2 | not from a PC: it is what a person types on Home, which is not in a file |
| [ppl.getkey-no-parentheses](topics/ppl.md#ppl.getkey-no-parentheses) | G2 | nothing to catch, and `lint` stays quiet |
| [ppl.matrices-by-value](topics/ppl.md#ppl.matrices-by-value) | G2 | `hpprime run`, held by `test_interp.py` |
| [ppl.expr-empty](topics/ppl.md#ppl.expr-empty) | G2 | lint rule `expr-empty` |
| [ppl.expr-dynamic-access](topics/ppl.md#ppl.expr-dynamic-access) | G2 | lint rule `expr-in-loop` |
| [ppl.global-namespace](topics/ppl.md#ppl.global-namespace) | G2 | lint rule `export-clash` |
| [ppl.decimal-point](topics/ppl.md#ppl.decimal-point) | G2 | not from a PC: a comma is also the argument separator, so F(3,5) reads the same either way |
| [ppl.compilation-order](topics/ppl.md#ppl.compilation-order) | G2 | not from a PC: which program was compiled first is the calculator's state |
| [ppl.check-last-error](topics/ppl.md#ppl.check-last-error) | emulator | not from a PC: it is what the calculator's editor shows |
| [ppl.speed-anchor](topics/ppl.md#ppl.speed-anchor) | G2 | not from a PC: it is a time, which only the calculator can take |
| [ppl.mu-zero-spelling](topics/ppl.md#ppl.mu-zero-spelling) | emulator | lint rule `mu-zero` |
<!-- End of the table written by `hpprime docs`. -->

## run

```bash
hpprime run FILE.txt --call "CIRCAREA(2)"
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

What it covers: numbers, strings and the string functions, lists, 1-based
matrices, `IF`/`CASE`/`FOR`/`WHILE`/`REPEAT`/`IFERR`, `EXPORT` functions,
globals and locals, matrices passed by value, and the native matrix algebra:
`MAKEMAT`, `MAKELIST`, `RREF`, `TRN`, `DET`, `INVERSE`, `IDENMAT`.

What it records instead of drawing: `TEXTOUT_P`, `RECT`, `INPUT`, `CHOOSE`,
`WAIT`, `MSGBOX` and `GETKEY`, including `GETKEY` written bare, without
parentheses, which is how PPL writes it. Each goes into `machine.io` and
returns a neutral value, so a program with an interface still runs end to end.

`GETKEY`'s neutral value is "no key pressed", so a loop that waits for one can
never finish here. That is the shape of every wait helper in this kit. Rather
than spin, a loop that has run a million times stops with a message naming the
cause: a tool that hangs with no output is worse than one that refuses.

What it does not cover raises, and never an invented result. If you need a
command, add it to `BUILTINS` with its case in `tests/test_interp.py`, and
measure it on the calculator first. These rules keep that promise where it
used to leak:

- A statement ends at `;`, at the keyword that closes its block, or at the
  end of the file. A word it cannot read after an expression makes that
  statement raise "not covered" when it is reached; it is never read as the
  next statement. That is how `9 MOD 4 + 100` once answered 9. The rest of
  the file still loads and runs.
- `MOD` and `NTHROOT` are written between their operands and bind as the
  emulator showed: `MOD` like `*` and `/`, left to right, with the sign of its
  divisor, and `NTHROOT` tighter than everything, `^` and a minus sign
  included. `MOD(9,4)` and `NTHROOT(3,8)` are refused, as the calculator
  refuses them. The entries, [MOD](commands/arithmetic/MOD.md) and
  [NTHROOT](commands/catalog/NTHROOT.md), have the rows.
- A list read at 0 answers its last element and one assigned at 0 grows, as
  on the emulator; an empty list, a string and a matrix read at 0 are errors
  ([ppl.one-based](topics/ppl.md#ppl.one-based)). A string indexed answers
  the character's code ([ppl.string-index-code](topics/ppl.md#ppl.string-index-code)).
- A name the calculator has and this does not implement, `Xmin` or `SSS`,
  raises "not covered", and so does a name with its app's name in front,
  `Statistics_1Var.MeanX`, which the calculator compiles and runs
  ([apps.qualified-names](topics/apps.md#apps.qualified-names)). Only a name
  that is on no list and that the program does not define is undefined.
- A builtin handed something it was not written for, `CONCAT` given a number
  or `FLOOR` a list, raises "not covered", naming it. The run prints one line
  and exits 1, never a Python traceback. So does a `--call` with anything
  after its expression.

That promise is checked against a source outside this repository.
`tests/hp_examples.txt` holds the worked examples from HP's own built-in help,
and `test_hpdocs.py` runs every one that applies. A command may answer HP's
number or refuse; answering a different number fails the suite. It found six on
its first run -- `ROUND` with a negative n, `MIN`/`MAX` over a list, `LOG` with
a base, `SORT` with a second argument, and `SIZE` of a matrix -- all since
corrected.

`LEFT`, `RIGHT`, `MID`, `INSTRING` and `SORT` are covered, every case measured
on a G2, including the trap that `LEFT(s,0)` and `RIGHT(s,0)` return the whole
string while `MID(s,start,0)` returns an empty one. What the calculator raises
on, this raises on, including a `MID` start below 1 and a `SORT` of a list
mixing numbers with strings, both of which are errors there.

One fidelity gap worth knowing: `M := GZ`, assigning a global matrix to a
local, aliases here and copies on the Prime. The way never to be bitten is not
to do it: work on the global.

## write / read / verify

```bash
hpprime write source.txt -o PROG.hpprgm     # build the binary
hpprime read PROG.hpprgm -o source.txt      # pull the source back out
hpprime verify PROG.hpprgm                  # round-trip check
hpprime verify MYAPP.hpappdir *.py          # app folder check
```

`write` uses `templates/code.hpprgm`, which the kit ships, unless you pass
`-t`. It reads back what it wrote before reporting success, and it refuses a
template that carries a compiled block, because changing the source would leave
that block out of step.

`read` works on anything with the container's magic, including the
`.hpappprgm` inside an app. Use it to compare what is installed with your
repository:

```bash
hpprime read ".../Calculators/HP Prime/MYPROG.hpprgm" -o installed.txt
diff installed.txt ppl/MYPROG.txt
```

`verify` takes either a `.hpprgm`, which it rebuilds and compares, or an app
folder, which it compares with what a build would produce. That is how you
catch the calculator having rewritten the wrappers.

It works out which kind of app it is looking at, because the two are not
compared the same way: a PPL app is built from the blank descriptor and its
`.hpappprgm` is supposed to differ from the empty skeleton. Give it the sources
too and it checks those as well; otherwise it says which parts it did not
compare.

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
rebuilt from the templates every time, on purpose. The calculator rewrites them
when you leave the app, and that state must not survive into your repository.

It also deletes `__pycache__`, which holds CPython `.pyc` files MicroPython
would not read, warns if a Python app has no `main.py`, and warns about imports
MicroPython does not have, which on the calculator show up as the app closing
at startup, silently. Use `--allow a,b` for modules you know are there. It
warns, too, on a call that hands `MOUSE` to Python as it is: `MOUSE` answers
lists inside lists, and a list that is not all numbers closes the app
([interface.mouse-lists](topics/interface.md#interface.mouse-lists)).

## install / pull

```bash
hpprime install CIRCLE.hpprgm --restart      # into the emulator, and open it
hpprime install MYAPP.hpappdir M1.hpmat      # apps and matrices too
hpprime pull                                 # what has it actually got?
hpprime pull CIRCLE --diff ppl/CIRCLE.txt    # is that my code? exits 1 if not
```

`install` copies into the Virtual Calculator's own folder, which, unlike the
Connectivity Kit's, is read by the emulator when it starts, so copying into it
installs. Measured end to end: the program appears in the Program Catalogue,
compiles, and runs.
[deploy.emulator-folder](topics/deploy.md#deploy.emulator-folder)
has the evidence and the three rules that follow from it.

It takes `.hpprgm` programs, `.hpappdir` folders and `.hpmat` matrices, and
refuses everything else, including a `.txt` source, because a calculator takes
that file without a word and then has nothing to run. A `.hpprgm` is opened and
parsed before it is copied, so a file that is not really one is caught here
rather than on the calculator.

Because the folder is read at startup, `install` also refuses to copy into a
running emulator: the copy would appear to work and change nothing. `--restart`
closes it, with a window-close request rather than a kill, so the calculator
saves itself, then copies and opens it again. With more than one calculator,
`--calc NAME` says which, and `hpprime doctor` lists them.

`pull` reads back what is really installed. The calculator rewrites each
program with its compiled block, so this is the state of the machine and not a
copy of what you meant to send. With no arguments it lists; with a name it
prints the source, or writes it with `-o`; with `--diff` it compares against
one of your files and exits 1 if they have drifted apart.

For a physical calculator neither of these applies. That is still a drag in the
CK window:
[deploy.ck-mirror](topics/deploy.md#deploy.ck-mirror).

## emu

```bash
hpprime emu list                  # every calculator, and which are clones
hpprime emu new LAB --from Prime  # one to experiment on
hpprime emu reset LAB             # back to how `new` left it
hpprime emu remove LAB
```

Calculators to burn, so that the one you care about is not the one you are
testing on. `new` clones a calculator that has been used -- the machine and its
built-in apps, none of your programs -- and gives it its own identity in
`settings`. It has to be cloned from a working one: a folder the emulator
created but never finished setting up asks for a language on every unlock and
never gets past it.

`reset` is the one that earns its place. A test that starts from a calculator
in a known state means something; one that starts from wherever you left it
last does not.

`remove` refuses a calculator it did not make, unless you pass `--force`.

Which calculator the emulator opens is not yours to choose. It takes the first
instance not already in use, in an order of its own: measured, with everything
free it opened `Prime` and not a clone called `LAB`, so it is not alphabetical.
`install --restart` says so when it is about to open a different one from the
one you installed into, and `compare` sidesteps it by sending to whichever one
the emulator does open.

## compare

```bash
hpprime compare lib.txt --call "CIRCAREA(2)" --call "F(3,350)"
hpprime compare --collect          # if you did not wait the first time
```

Runs the same calls here and on the calculator, and puts the two columns side
by side. `hpprime run` is not the Prime's interpreter, and the only way to find
where they disagree is to ask both.

The results come back as a file rather than off the screen: a generated wrapper
stores each result into `M9`, the emulator writes `M9.hpmat` into its
calculator folder when it closes, and
[formats.md](topics/formats.md) is already able to decode that. So the loop
is: it installs, you type `HPKCMP` on the calculator and close the emulator,
and the table appears.

```
call         here               calculator
-----------  -----------------  -----------------  ------------
CIRCAREA(2)  12.56636           12.56636           same
F(3,350)     1050.0             1050.0             same
```

It exits 1 if any row disagrees, so it works as a gate.

What to know:

- Numbers only. A matrix cell holds one, so a call whose answer is a string or
  a list is recorded as "did not give a number" on both sides. That is a real
  answer, since both refusing counts as agreement, but it is not the value.
- One keypress is yours. Nothing on the Prime starts a program by itself, so
  the wrapper has to be run once by hand. Whether an app's `START` hook fires
  at boot, which would remove even that, is not measured.
- The generated program goes through the linter before it is sent, and an
  error stops it. The wrapper passes: `CIRCAREA(0)` in it calls a function your
  code defines, so the 0 is an argument and not an index.
- `--mat N` if `M9` is in use, `--tol X` for how close counts as the same
  (default 1e-9, relative), `--keep` to leave the wrapper on the calculator.

## matrix

```bash
hpprime matrix read  M1.hpmat -o data.csv
hpprime matrix write data.csv -o M0.hpmat
hpprime matrix nums  PROG.hpprgm
```

`.hpmat` files are the `M0`..`M9` matrices, and the file name decides which
one. This lets a whole matrix reach the calculator as a file, with nothing
pasted.

`nums` walks a program's compiled block and reports every symbol in it, with
the matrices decoded and other types named but not read. It is for looking, not
for writing: whether a calculator accepts a block you generate is unmeasured.
The grammar is in
[formats.md](topics/formats.md#formats.symbol-table).

Complex matrices raise an explicit error rather than returning invented
numbers.

## examples

```bash
hpprime examples LEFT RIGHT            # these entries' examples, one batch
hpprime examples --all                 # every entry's examples
hpprime examples LEFT --probe 'LEFT=LEFT("abc", -2)'   # and a call no entry states
hpprime examples --collect             # read a batch you did not wait for
hpprime examples --collect --replace   # and let different answers replace stored rows
hpprime examples --relabel             # HP help or unverified -> emulator where it agrees
hpprime examples --compile probes.txt  # does each of these programs compile?
```

Runs the documentation's examples on the Virtual Calculator and keeps what it
answers in `docs/commands/results.tsv`. What that file means for an entry is
in [format.md](format.md).

Every call goes into one generated program, `HPKDOC`, inside `IFERR`, and its
answer comes back through `M9`, one row per call: whether it answered, `TYPE`,
the number when it is one, and `STRING` of the answer as character codes, so
text, lists and matrices come back as well as numbers. The first row holds
what the calculator says `VERSION` is, and every result is stored with it.

The batch runs on a calculator called `Prime_1`, cloned from yours the first
time and reset before every batch, so every answer comes from the same state
and your own calculator is not touched. The name is the emulator's choice, not
the kit's: the first window opens `Prime`, the second `Prime_1`, and no window
opens a calculator with any other name
([deploy.emulator-folder](topics/deploy.md#deploy.emulator-folder)).
So the command launches only when the next window will be `Prime_1`, which it
reads from the emulator's lock files, and otherwise says what to open or close
first: usually, open your own calculator in the emulator before you run it. A
`Prime_1` the kit did not make is moved into the kit's own folder, never
deleted. When that window closes, the saved state of `Prime_1` has to have
moved, or nothing is read.

Your part is three steps in that emulator, and the command prints them and
waits: compile `HPKDOC` once (`Check` in its editor, since a program copied as
a file is not live on Home until then), run it from Home, and close the
window.

What is stored is the evidence, so nothing replaces it or loses it without a
word:

- A row `results.tsv` already holds is not replaced by a different answer.
  The report shows the stored answer as `KEPT`, the command exits 1, and
  `--collect --replace` lets the new one in. Which of the two is right is
  yours to settle: an app active in one run and not in the other has done
  this. The same answer again is written, with the new date.
- A `--probe` whose entry and call already have a row is refused before the
  emulator opens, unless `--replace` is given, since collecting it would
  replace that row.
- An answer whose cells cannot be read costs its own row, not the batch. When
  only the number is unreadable, the row is kept from its text, which is the
  answer as an entry writes it; otherwise the report says `UNREADABLE` and
  nothing is stored for that call. The two infinities are read
  ([formats.number-infinity](topics/formats.md#formats.number-infinity)).
- A row carries the day `M9.hpmat` was written, which is when the emulator
  closed after running the batch, not the day it was prepared.

Whether something compiles is a question a batch cannot ask: a program that
does not compile takes the whole batch with it. `--compile` takes a file of
small programs, each headed by the fact or entry it answers and its name:

```
[ppl.local-limit] ZQL09
EXPORT ZQL09()
BEGIN
  LOCAL za,zb,zc,zd,zf,zg,zh,zj,zk;
  RETURN 1;
END;
```

They go on `Prime_1` with `HPKDOC` and two controls: `ZCOK`, which compiles,
and `ZCBAD`, which uses `ENDIF` and does not
([ppl.no-end-keywords](topics/ppl.md#ppl.no-end-keywords)). You press
`Check` on each, in the order printed, whatever it says, then run `HPKDOC`
and close the window. The emulator writes a compiled block into a program's
file once it compiles
([deploy.emulator-folder](topics/deploy.md#deploy.emulator-folder)), so the
file says whether it did. **If `ZCOK` has no block, or `ZCBAD` has one, the
method did not work and nothing is concluded or stored.** Otherwise each
program's answer, `*compiles*` or `*does not compile*`, is stored under its
fact with the source as its call. `--probe` calls in the same run go into
`HPKDOC`, which is how a program that compiled is then run: a zero-argument
one as `EXPR("NAME")`.

## docs

```bash
hpprime docs            # check the entries, then regenerate the pages made from them
hpprime docs --check    # change nothing; exit 1 if anything is wrong
```

The documentation under `docs/commands/` and `docs/topics/` follows one
format, stated in [format.md](format.md), and this command holds it to that
format. Every entry has its fields in order; every example and every
behaviour paragraph carries a label saying how it is known; names and fact
identifiers are unique, and every link to one resolves; nothing in it
points at the layer built on top of it; and nothing speaks of how it was
built, such as a phase of the work or "this kit".

For a command that `hpprime run` implements, every example goes through the
interpreter and has to give the result the entry states. An example the
interpreter does not cover is listed as a note rather than failed, for the
same reason `run` raises instead of guessing. Every example also has to have
been run somewhere: an answer stored from the Virtual Calculator, a
measurement on a G2, or the interpreter. One that has none fails.

The group pages, `docs/commands/<group>.md`, the two indexes and
`docs/llms.txt`, the index a model loads first, are generated from the
entries and the facts. `--check` fails when one of them is out of date or
`docs/llms.txt` passes its budget of 100,000 bytes, and so does
`tests/test_reference.py`.

## templates

```bash
hpprime templates "C:\Users\you\Documents\HP Connectivity Kit\Calculators"
```

Says which of your `.hpprgm` files can act as a template for `write`. You need
this only if the shipped template ever fails you, and it is not obvious by eye,
because the mirror folder holds files that have been through the calculator,
which adds a compiled block to everything it saves. Measured on one machine: 2
of 58 qualified.

---

## Testing the kit itself

```bash
python tests/run_all.py
```

Fourteen suites, and none of them needs a calculator. Two use one if it is there:
the `.hpprgm` reader against your own binaries, and the number format against
your own data. They skip what they cannot find rather than failing.

| Suite | What it covers |
|---|---|
| `test_lint.py` | that the linter catches, and that it does not raise false alarms |
| `test_interp.py` | the interpreter's subset, and that it fails where it must |
| `test_program.py` | the shipped template, and round trips over your binaries |
| `test_appdir.py` | building an app, and what `verify` sees |
| `test_numbers.py` | the internal number format, against real encodings |
| `test_cli.py` | the whole `hpprime` path a newcomer walks |
| `test_update.py` | `update` on a folder and ZIPs made in the test: what it writes, and what it must never touch |
| `test_examples.py` | the starters and examples, so the first thing anybody copies still works |
| `test_docs.py` | every relative link in the documentation resolves |
| `test_hpdocs.py` | the interpreter against the examples in HP's own help |
| `test_emulator.py` | installing into the emulator and reading back, with a temp folder standing in for a calculator |
| `test_compare.py` | the generated wrapper, and the comparison, against a matrix written as the calculator would have left it |
| `test_reference.py` | the documentation's format, held in both directions: each way of breaking it is caught, and the real pages pass |
| `test_examples_run.py` | `hpprime examples` without the emulator: the program it generates, the answers read back, `results.tsv`, relabelling, and a stand-in that writes the matrix as the calculator would |

## Using the modules directly

Every command is a thin front over a module you can import:

```python
from hpkit import lint, interp, program, appdir, numbers, emulator, compare, docs, examples, update
```

| Module | Main entry points |
|---|---|
| `lint` | `check_source(path, text)`, `check_files(paths)` |
| `interp` | `Machine()`, `.load_file()`, `.call()`, `.io` |
| `program` | `read(data)`, `write(template, source)`, `default_template()` |
| `appdir` | `build()`, `check()`, `put_ppl_program()`, `check_imports()` |
| `numbers` | `decode()`, `encode()`, `read_hpmat()`, `write_hpmat()` |
| `emulator` | `find_root()`, `instances()`, `pick()`, `install()`, `contents()`, `source_of()`, `create()`, `reset()` |
| `compare` | `harness()`, `here()`, `there()`, `verdicts()` |
| `examples` | `cases()`, `harness()`, `decode()`, `read_results()`, `write_results()`, `run()`, `collect()`, `relabel()` |

# Working in this repository

For any AI agent -- Claude Code, Cursor, Copilot, Codex or another -- writing
HP Prime code with a human, or changing this kit itself.

The person you are working with probably cannot check your PPL by reading it,
and the calculator will not explain it either: it answers `syntax error` and a
line number. So the burden of proof is on you, and this repository exists to
let you carry it without a calculator.

---

## 1. Before you write a line of PPL

Load [`docs/llms.txt`](docs/llms.txt) first. It is the index of the
documentation: every fact and every command entry on one line, with its link
and a one-line summary, kept small enough to load whole. Follow the links you
need from there. Whether a name exists at all is in
[`docs/commands/names.tsv`](docs/commands/names.tsv), HP's own list. A name that
is not on it is somebody else's or nobody's, and
[`docs/commands/not-hp.tsv`](docs/commands/not-hp.tsv) says which.

Then read [`docs/topics/ppl.md`](docs/topics/ppl.md): the limits that break
compilation, and six hypotheses that look reasonable and are false, each
marked `refuted hypothesis`. Writing PPL from memory means inventing
restrictions that do not exist and missing the ones that do.

Then, depending on the task:

| Task | Read |
|---|---|
| the user has never programmed a Prime | [`docs/start/01-setup.md`](docs/start/01-setup.md), and send them there before anything else |
| anything in PPL | [`docs/topics/ppl.md`](docs/topics/ppl.md) |
| screens, keys, touch | [`docs/topics/interface.md`](docs/topics/interface.md) |
| choosing how to build a screen, or using somebody's library | [`docs/topics/libraries.md`](docs/topics/libraries.md) |
| wrapping it as an app | [`docs/topics/apps.md`](docs/topics/apps.md) |
| writing it in Python | [`docs/topics/micropython.md`](docs/topics/micropython.md) |
| the binary formats, or moving a lot of data | [`docs/topics/formats.md`](docs/topics/formats.md) |
| getting it onto the calculator | [`docs/topics/deploy.md`](docs/topics/deploy.md) |
| seeing a connected G2's screen, or pressing its keys | [`docs/topics/usb.md`](docs/topics/usb.md) |
| one PPL command | its entry, linked from [`docs/llms.txt`](docs/llms.txt) |
| every `hpprime` command | [`docs/tools.md`](docs/tools.md) |
| how other apps are laid out, as options | [`docs/patterns.md`](docs/patterns.md) |
| what was run to measure a fact | [`docs/evidence/README.md`](docs/evidence/README.md): measurements and not examples to copy, and some do not compile on purpose |

The non-negotiables, as a checklist. Each names the fact that holds it, with
its evidence, in `ppl.md`:

- Indexes start at 1. A 0 is never the first element: for `MID` and a
  matrix it is an error, and a list read at 0 answers its LAST element
  (`ppl.one-based`).
- `:=` assigns, `==` compares, `<>` is not-equal (`ppl.equality-operators`).
- `END` closes every block. `ENDIF`, `ENDFOR` and `ENDWHILE` do not exist
  (`ppl.no-end-keywords`), and `END` takes its `;` (`ppl.end-semicolon`).
- At most 8 variables per `LOCAL` statement (`ppl.local-limit`). A `LOCAL` can
  go after other statements (`ppl.locals-at-top`), and used after the end of its
  block it does not compile (`ppl.local-block-scope`).
- `x = 2;` as a statement assigns nothing, silently: assign with `:=`
  (`ppl.equality-operators`).
- You cannot index the result of a call: `SIZE(M)(1)` does not compile
  (`ppl.index-call`).
- Exported names are global and collide, with each other and with HP's own
  names. Prefix them (`ppl.global-namespace`). One of Home's variables does not
  even compile: `EXPORT Z := 1;`, and a function called `F` compiles, but typed on
  Home `F` is the variable (`ppl.export-home-variable`). One `EXPORT` holds at most
  8 variables (`ppl.export-initialised`).
- On Home, tell somebody to type a zero-argument function without parentheses,
  `MYFUNC`: `MYFUNC()` is a syntax error there, except on the RPN stack. Get this
  right whenever you tell somebody how to test on the calculator
  (`ppl.home-no-parentheses`). In source, both forms work
  (`ppl.call-no-parentheses`).
- When you name a function to somebody, say whose it is: HP's, which comes with
  the calculator; a library's, which has to be installed first
  (`libraries.published`, `unverified`), since a program that calls it does not
  compile without it (`ppl.compilation-order`); or one written here. The words
  are in [`docs/format.md`](docs/format.md#where-a-name-comes-from).

## 2. The workflow to follow

How the app is built is the person's choice. The documentation says what the
calculator does, and [`docs/patterns.md`](docs/patterns.md) holds ways other
apps are built, each with its costs. Do not present a pattern as a rule, and do
not restructure somebody's program to fit one unless they ask.


A person's programs go in [`programs/`](programs/README.md), one folder each:
`programs/NAME/` holds the source and the `.hpprgm` built from it. Never write
theirs at the root, in `examples/` or in `templates/`, which ship with the kit.
Run the tools from the root, with the path:
`hpprime write programs/NAME/NAME.txt -o programs/NAME/NAME.hpprgm`.

The tools need Python 3.7 or newer. If `python --version` does not print a
version -- on Windows a missing Python can answer that it was not found, or
open the Microsoft Store -- stop there and send the person to the Python row of
[step 1](docs/start/01-setup.md#what-to-install), instead of trying other
commands.

Never hand over PPL that has not been through both gates:

```bash
hpprime lint FILE.txt                       # 0 errors, or fix and repeat
hpprime run  FILE.txt --call "CIRCAREA(2)"   # the right answer, not just no error
```

Then, and only then:

```bash
hpprime write FILE.txt -o PROG.hpprgm
```

`lint` catches what the compiler will not explain. `run` executes the actual
file, and raises rather than inventing a result when a command is not covered,
so a clean run means something. A program that is all screen and keys may have
nothing `run` can answer on the PC: then `hpprime run FILE.txt`, with no
`--call`, shows that it loads, and what it does is for the calculator to show.
Say so plainly.

For an app, `hpprime build` and then `hpprime verify`.

To try it on the emulator, which you can do yourself:

```bash
hpprime install PROG.hpprgm --restart   # copies, and opens the emulator
hpprime pull PROG --diff FILE.txt       # what is really installed; exits 1 if
                                        # it is not your file
```

Do not claim that the PC run and the calculator agree unless you have checked:

```bash
hpprime compare FILE.txt --call "CIRCAREA(2)"   # both columns, side by side
```

That needs the user to type `HPKCMP` on the calculator once and close the
emulator. Ask for it rather than asserting that the two agree.

On a G2 on its cable, on Windows and with the Kit closed, you can install a
program, see the screen and press the keys yourself. Ask before closing the
Kit, before sending, which replaces a program of that name without asking, and
before any key that changes what the calculator holds:

```bash
hpprime send FILE.txt           # installs; a clean exit says only that it was sent
hpprime screen -o now.png       # what it is showing; open the picture and look
hpprime type CIRCAREA --enter   # a name and Enter: letters and digits only
hpprime press up                # keys; a clean exit says only that they were sent
```

The person may be using the calculator for their own work: look at the screen
before any key, and if you leave a view, go back to it. Opening the Kit can open a
firmware update with its button focused (`deploy.ck-offers-firmware`, `G2`): send
that window no key, and leave the decision to the person.

An app on a physical calculator is still the user dragging its folder onto it in
the Connectivity Kit window, and so is a program for anyone who prefers that. Do
not tell them to copy into the CK's mirror folder: that installs nothing.

If you have shell access, run these yourself. Do not ask the user to relay
output you could have obtained.

In Claude Code, hooks in [`.claude/settings.json`](.claude/settings.json)
hold you to this for programs in `programs/`: after every edit `lint`
answers, and your turn cannot end until every program you edited has passed
`lint` on its current content and `run` has at least loaded it, and every fact
you cite exists. A program you only loaded is named to the person.
Switching them off is the person's decision (`"disableAllHooks": true` in
their `.claude/settings.local.json`), never yours. They start `python`, so where
only `python3` starts they do not run: then the gates are yours to keep.

## 3. What you must not claim

Nothing works until a command says it does.

- Do not say a program compiles. Say the linter is clean, and paste what it
  printed.
- Do not say it computes correctly. Say what `hpprime run --call` returned.
- Do not say a program is installed on hardware because `hpprime send` exited
  0. Nothing acknowledges it (`usb.send-program`, `G2`): say what it answered
  when you ran it. An app you cannot install: dragging it onto the calculator in
  the Connectivity Kit window is the human's job, and the mirror folder is not a
  mailbox. On the emulator you can do either, and then `hpprime pull` says what
  is really there. See [`deploy.md`](docs/topics/deploy.md).
- Do not say a key did something because `hpprime press` exited 0. Nothing
  acknowledges a key (`usb.keys`, `G2`): say what `hpprime screen` shows after
  it.
- Do not report a platform fact without evidence. If it is in
  `docs/topics/`, cite the fact by its identifier and its label; if it is
  about one command, cite its entry. If you measured it, say how. If neither,
  say you are not sure. A fact labelled `unverified` is not evidence either,
  and says so. On this platform a confident wrong number is expensive,
  because nothing contradicts it until the calculator does.

## 4. When something fails

An error that does not move after a fix means the hypothesis is false, not that
the fix was too small. Change tack rather than trying a fourth variation.

What works here is not reasoning about syntax. It is measuring programs that
already run on that same calculator, and comparing. Two practical forms of
that:

- If the linter is clean and the calculator still refuses the program, it is a
  case nobody has measured. Ask the user for the exact message and line,
  compare against code known to compile, and when you find the rule, add it
  (see §6).
- If the linter refuses what you have reason to believe compiles, the rule may
  be the mistake: `ppl.locals-at-top` was one. Read its fact's evidence. On a G2
  you can ask the calculator, with the person's approval: `hpprime send --no-lint`
  and `usb.compile-check` (`G2`).
- If a Python app closes on startup with no message, do not guess. Use a probe
  that leaves a mark in a PPL global after each step, in order of increasing
  risk: [`micropython.md`](docs/topics/micropython.md#micropython.mark-debugging), with one ready
  to run in `examples/probe/`.

## 5. Time you will otherwise waste

- hpmuseum.org blocks automated access and answers with a challenge you cannot
  pass. Do not try. For HP Prime material, the source that does allow reading
  is hpcalc.org.
- Reading somebody's working app beats any tutorial. The event loop, the key
  codes and the menu geometry documented here all came from downloading apps
  and reading them.
- `time` does not exist in MicroPython on the Prime. If `import time` fails,
  the bridge is fine and the module is not there (`micropython.modules`,
  `unverified`).
- The Calculators folder is a mirror, and it is often empty. That is not a
  broken installation.

## 6. If you change this kit

- Everything is in English: code, comments, messages, docs, commit messages.
- Tests must pass: `python tests/run_all.py`. None of them needs a calculator.
  If you add a rule or a builtin, add its case.
- A new platform fact needs evidence: which program, which firmware, what was
  seen. It goes in the reference page it belongs to. If it can be caught from
  the PC, it also gets a linter rule and a test. What has not been measured is
  marked `Unverified` rather than stated as fact. See
  [`CONTRIBUTING.md`](CONTRIBUTING.md).
- One fact, one home. If it is in `docs/topics/`, link to it; do not restate
  it. The one deliberate exception is
  [`docs/ai/prompts.md`](docs/ai/prompts.md) §1, a context block for chats that
  cannot read files, and it says so.
- No anecdotes, no achievement numbers, no narrative. State the fact and how it
  is known.
- Do not add dependencies. Python 3.7+, standard library only, no install step.

## 7. What only the human can do

Say so plainly when you reach these, instead of implying you have done them:

- installing an app on a physical calculator (a program you can send yourself
  to a G2 with `hpprime send`, and the emulator you can do with
  `hpprime install`);
- running a program on the emulator: `hpprime compare` sends one and reads
  its numbers back, but somebody has to press the key that starts it. On a G2
  on its cable you can start one yourself with `hpprime type NAME --enter`, at
  about 3 s a key, and read its answer with `hpprime screen`. Read that answer:
  Home does not always refuse a name it does not know (`usb.start-by-name`,
  `G2`);
- confirming a program runs on hardware, beyond typing its name and reading its
  answer: what it draws and how it takes keys has not been watched over USB.
  The emulator is close, not identical, and every fact in `docs/topics/`
  labelled `unverified` is waiting for exactly this;
- timing anything, and judging whether an interface is usable in practice.
